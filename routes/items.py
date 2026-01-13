import os
from flask import Blueprint, render_template, request, session, jsonify
from werkzeug.utils import secure_filename
from db import get_db

items_bp = Blueprint('items', __name__)

@items_bp.route("/", methods=["GET"])
def item_list():
    user_id = session.get("user_id") or 1
    db = get_db()
    sort = request.args.get("sort") or "newest"
    selected_category = request.args.get("category")

    if sort == "newest":
        order_by = "items.id DESC"
    elif sort == "num_items_desc":
        order_by = "items.quantity DESC"
    elif sort == "num_items_asc":
        order_by = "items.quantity ASC"
    else:
        order_by = "items.name DESC"

    categories = db.execute("SELECT name FROM categories").fetchall()

    category_condition = ""
    params = [user_id]

    if selected_category and selected_category != "全てのアイテム":
        category_condition = " AND categories.name = ?"
        params.append(selected_category)

    sql = f"""
        SELECT items.id, items.name, items.quantity, items.image_path,
               GROUP_CONCAT(categories.name) AS categories
        FROM items
        JOIN item_categories ON items.id = item_categories.item_id
        JOIN categories ON categories.id = item_categories.category_id
        WHERE items.user_id = ? {category_condition}
        GROUP BY items.id
        ORDER BY {order_by}
    """
    item_rows = db.execute(sql, params).fetchall()

    items=[]
    for item_row in item_rows:
        items.append({
            "id": item_row["id"],
            "name": item_row["name"],
            "quantity": item_row["quantity"],
            "image_path": item_row["image_path"],
            "categories": item_row["categories"].split(",") if item_row["categories"] else []
        })
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("components/item_list.html", items=items)

    return render_template("index.html", items=items, categories=categories)

@items_bp.route('/items/search/results', methods=["GET"])
def item_seach():
    db = get_db()
    user_id = session.get("user_id") or 1
    sort = request.args.get("sort") or "newest"
    selected_category = request.args.get("category")
    selected_keyword = request.args.get("keyword")
    selected_quantity = request.args.get("quantity")

    if sort == "newest":
        order_by = "items.id DESC"
    elif sort == "num_items_desc":
        order_by = "items.quantity DESC"
    elif sort == "num_items_asc":
        order_by = "items.quantity ASC"
    else:
        order_by = "items.name DESC"

    categories = db.execute("SELECT name FROM categories").fetchall()

    conditions = ["items.user_id = ?"]
    params = [user_id]

    if selected_category and selected_category != "全てのアイテム":
        conditions.append("categories.name = ?")
        params.append(selected_category)
    if selected_keyword:
        conditions.append("(items.name LIKE ? OR items.description LIKE ?)")
        params.extend([
            f"%{selected_keyword}%",
            f"%{selected_keyword}%"
        ])
    if selected_quantity == "in":
        conditions.append("items.quantity > 0")
    elif selected_quantity == "out":
        conditions.append("items.quantity = 0")

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT items.id, items.name, items.quantity, items.image_path,
               GROUP_CONCAT(categories.name) AS categories
        FROM items
        JOIN item_categories ON items.id = item_categories.item_id
        JOIN categories ON categories.id = item_categories.category_id
        WHERE {where_clause}
        GROUP BY items.id
        ORDER BY {order_by}
    """
    item_rows = db.execute(sql, params).fetchall()

    items=[]
    for item_row in item_rows:
        items.append({
            "id": item_row["id"],
            "name": item_row["name"],
            "quantity": item_row["quantity"],
            "image_path": item_row["image_path"],
            "categories": item_row["categories"].split(",") if item_row["categories"] else []
        })
    return render_template("components/item_list.html", items=items)


@items_bp.route("/items/<int:item_id>/modal", methods=["GET"])
def item_modal(item_id):
    db= get_db()
    sql = f"""
        SELECT items.id, items.name, items.quantity, items.image_path,
               GROUP_CONCAT(categories.name) AS categories
        FROM items
        JOIN item_categories ON items.id = item_categories.item_id
        JOIN categories ON categories.id = item_categories.category_id
        WHERE {where_clause}
        GROUP BY items.id
        ORDER BY {order_by}
    """
    if not item_row:
        return "Not Found", 404
    item = {
        "id": item_row["id"],
        "name": item_row["name"],
        "description": item_row["description"],
        "quantity": item_row["quantity"],
        "image_path": item_row["image_path"],
        "work_title": item_row["work_title"],
        "character_name": item_row["character_name"],
        "categories": item_row["categories"].split(",") if item_row["categories"] else []
    }
    return render_template("components/item_modal.html", item=item)
    
@items_bp.route('/items/create', methods=['GET'])
def item_create_form():
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template("item_new.html", mode="create", categories=categories)


@items_bp.route("/items/create", methods=["POST"])
def item_create():
    db = get_db()
    user_id = session.get("user_id") or 1

    name = request.form.get("name")
    quantity = request.form.get("quantity", 1)
    work_title = request.form.get("work_title")
    character_name = request.form.get("character_name")
    description = request.form.get("description", "").strip()
    if description == "" or description.lower() == "none":
        description = None
    category = request.form.get("category")
    image_file = request.files.get("image_file")


    errors = []
    if not name:
        errors.append("グッズ名は必須です")

    if not category or category.strip() == "":
        errors.append("カテゴリーを選択してください")
        
    if not image_file or image_file.filename == "":
        errors.append("画像は必須です")

    if errors:
        return jsonify({"errors": errors}), 400
    
    # 画像ファイルの保存
    filename = secure_filename(image_file.filename)
    upload_dir = os.path.join("static", "images")
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, filename)
    image_file.save(save_path)
    image_path = filename

    #カテゴリーIDの取得または作成
    category_row = db.execute(
        "SELECT id FROM categories WHERE name = ?",
        (category,)
    ).fetchone()
    if category_row:
        category_id = category_row["id"]
    else:
        cursor = db.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (category,)
        )
        category_id = cursor.lastrowid

    # データベースにアイテムを保存
    cursor = db.execute("""
        INSERT INTO items (user_id, name, image_path, quantity, work_title, character_name, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, image_path, quantity, work_title, character_name, description)
    )
    item_id = cursor.lastrowid
    db.execute(
        "INSERT INTO item_categories (item_id, category_id) VALUES (?, ?)",
        (item_id, category_id)
    )

    db.commit()
    return jsonify({"status": "success"})

@items_bp.route('/items/<int:item_id>/edit', methods=['GET'])
def item_edit_form(item_id):
    db = get_db()
    item_row = db.execute(
        "SELECT * FROM items WHERE id = ?",
        (item_id,)
    ).fetchone()
    if not item_row:
        return "Not Found", 404

    category_row = db.execute(
        """
        SELECT categories.name
        FROM categories
        JOIN item_categories ON categories.id = item_categories.category_id
        WHERE item_categories.item_id = ?
        """,
        (item_id,)
    ).fetchone()
    category_name = category_row["name"] if category_row else ""
    categories = db.execute("SELECT * FROM categories").fetchall()

    item = {
        "id": item_row["id"],
        "name": item_row["name"],
        "quantity": item_row["quantity"],
        "work_title": item_row["work_title"],
        "character_name": item_row["character_name"],
        "description": item_row["description"],
        "image_path": item_row["image_path"],
        "category": category_name
    }
    return render_template("item_new.html", mode="edit", item=item, categories=categories)

@items_bp.route('/items/<int:item_id>/update', methods=['POST'])
def item_update(item_id):
    db = get_db()
    user_id = session.get("user_id") or 1

    name = request.form.get("name")
    quantity = request.form.get("quantity", 0)
    work_title = request.form.get("work_title")
    character_name = request.form.get("character_name")
    description = request.form.get("description", "").strip()
    if description == "" or description.lower() == "none":
        description = None
    category = request.form.get("category")
    image_file = request.files.get("image_file")

    errors = []
    if not name:
        errors.append("グッズ名は必須です")

    if not category or category.strip() == "":
        errors.append("カテゴリーを選択してください")

    if quantity is None or quantity == "":
        errors.append("個数は必須です")
    else:
        try:
            if int(quantity) < 0:
                errors.append("個数は0以上で入力してください")
        except ValueError:
            errors.append("個数は数字で入力してください")

    if errors:
        return jsonify({"errors": errors}), 400

    old_item = db.execute(
        "SELECT image_path FROM items WHERE id = ? AND user_id = ?",
        (item_id, user_id)
    ).fetchone()

    if not old_item:
        return "Not Found", 404

    image_path = old_item["image_path"]

    # 画像が新しく来たときだけ差し替え
    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        upload_dir = os.path.join("static", "images")
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        image_file.save(save_path)
        image_path = filename

    # カテゴリーIDの取得 or 作成
    category_row = db.execute(
        "SELECT id FROM categories WHERE name = ?",
        (category,)
    ).fetchone()

    if category_row:
        category_id = category_row["id"]
    else:
        cursor = db.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (category,)
        )
        category_id = cursor.lastrowid

    # items 更新
    db.execute("""
        UPDATE items
        SET name = ?, image_path = ?, quantity = ?, work_title = ?, character_name = ?, description = ?
        WHERE id = ? AND user_id = ?
    """, (name, image_path, int(quantity), work_title, character_name, description, item_id, user_id))

    # item_categories 更新（1カテゴリ想定）
    db.execute("DELETE FROM item_categories WHERE item_id = ?", (item_id,))
    db.execute(
        "INSERT INTO item_categories (item_id, category_id) VALUES (?, ?)",
        (item_id, category_id)
    )

    db.commit()
    return jsonify({"status": "success"})
    
@items_bp.route('/items/<int:item_id>/delete', methods=['POST'])
def item_delete(item_id):
    db = get_db()
    user_id = session.get("user_id") or 1

    db.execute(
        "DELETE FROM items WHERE id = ? AND user_id = ?",
        (item_id, user_id)
    )
    db.commit()
    return jsonify({"status": "success"})

    
