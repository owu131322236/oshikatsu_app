import os
from flask import Blueprint, render_template, request, session, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import text
from db import SessionLocal

items_bp = Blueprint('items', __name__)

@items_bp.route("/", methods=["GET"])
def item_list():
    user_id = session.get("user_id") or 1
    db = SessionLocal()
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

    categories = db.execute(text("SELECT name FROM categories")).mappings().all()

    category_condition = ""
    params = {}
    where = ["items.user_id = :user_id"]
    params["user_id"] = session.get("user_id") or 1

    if selected_category and selected_category != "全てのアイテム":
        category_condition = f"AND categories.name = :category_name"
        params["category_name"] = selected_category

    where = " AND ".join(where)
    sql = f"""
    SELECT items.id, items.name, items.quantity, items.image_path,
        STRING_AGG(categories.name, ',') AS categories
    FROM items
    JOIN item_categories ON items.id = item_categories.item_id
    JOIN categories ON categories.id = item_categories.category_id
    WHERE {where} GROUP BY items.id, items.name, items.quantity, items.image_path
    """

    item_rows = db.execute(text(sql), params).mappings().all() 
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
def item_search():
    db = SessionLocal()
    user_id = session.get("user_id") or 1
    sort = request.args.get("sort") or "newest"
    selected_category = request.args.get("category")
    selected_keyword = request.args.get("keyword")
    selected_quantity = request.args.get("quantity")

    order_map = {
        "newest": "items.id DESC",
        "num_items_desc": "items.quantity DESC",
        "num_items_asc": "items.quantity ASC",
        "name": "items.name DESC"
    }
    order_by = order_map.get(sort, "items.id DESC")
    categories = db.execute(text("SELECT name FROM categories")).mappings()

    conditions = ["items.user_id = :user_id"]
    params = {"user_id": user_id}

    if selected_category and selected_category != "全てのアイテム":
        conditions.append("categories.name = :category_name")
        params["category_name"] = selected_category

    if selected_keyword:
        conditions.append("(items.name LIKE :kw OR items.description LIKE :kw)")
        params["kw"] = f"%{selected_keyword}%"

    if selected_quantity == "in":
        conditions.append("items.quantity > 0")
    elif selected_quantity == "out":
        conditions.append("items.quantity = 0")

    where_clause = " AND ".join(conditions)

    sql = f"""
    SELECT items.id, items.name, items.quantity, items.image_path,
           STRING_AGG(categories.name, ',') AS categories
    FROM items
    JOIN item_categories ON items.id = item_categories.item_id
    JOIN categories ON categories.id = item_categories.category_id
    WHERE {where_clause}
    GROUP BY items.id, items.name, items.quantity, items.image_path
    ORDER BY {order_by}
    """

    item_rows = db.execute(text(sql), params).mappings().all()

    # --- 結果整形 ---
    items = []
    for row in item_rows:
        items.append({
            "id": row["id"],
            "name": row["name"],
            "quantity": row["quantity"],
            "image_path": row["image_path"],
            "categories": row["categories"].split(",") if row["categories"] else []
        })

    return render_template("components/item_list.html", items=items)


@items_bp.route("/items/<int:item_id>/modal", methods=["GET"])
def item_modal(item_id):
    db= SessionLocal()
    sql = text("""SELECT items.id,items.name,items.description,items.quantity,items.image_path,items.work_title,items.character_name,STRING_AGG(categories.name, ',') AS categories FROM items JOIN item_categories ON items.id = item_categories.item_id JOIN categories ON categories.id = item_categories.category_id WHERE items.id = :item_id GROUP BY items.id, items.name, items.description, items.quantity, items.image_path, items.work_title, items.character_name""")

    item_row = db.execute(sql, {"item_id": item_id}).mappings().fetchone()
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
    return render_template(
        "components/item_modal.html",
        item=item
    )
@items_bp.route('/items/create', methods=['GET'])
def item_create_form():
    db = SessionLocal()
    categories = db.execute(text("SELECT name FROM categories")).fetchall()
    return render_template("item_new.html", mode="create", categories=categories)


@items_bp.route("/items/create", methods=["POST"])
def item_create():
    db = SessionLocal()
    user_id = session.get("user_id") or 1

    name = request.form.get("name")
    quantity = request.form.get("quantity", 1)
    work_title = request.form.get("work_title")
    character_name = request.form.get("character_name")
    description = request.form.get("description", "").strip() or None
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

    filename = secure_filename(image_file.filename)
    upload_dir = os.path.join("static", "images")
    os.makedirs(upload_dir, exist_ok=True)
    image_file.save(os.path.join(upload_dir, filename))
    image_path = filename

    category_sql = text("SELECT id FROM categories WHERE name = :name")
    category_row = db.execute(category_sql, {"name": category}).mappings().fetchone()

    if category_row:
        category_id = category_row["id"]
    else:
        insert_cat_sql = text("INSERT INTO categories (name) VALUES (:name) RETURNING id")
        category_id = db.execute(insert_cat_sql, {"name": category}).fetchone()["id"]

    insert_item_sql = text("""
        INSERT INTO items (user_id, name, image_path, quantity, work_title, character_name, description)
        VALUES (:user_id, :name, :image_path, :quantity, :work_title, :character_name, :description)
        RETURNING id
    """)
    item_id = db.execute(insert_item_sql, {
        "user_id": user_id,
        "name": name,
        "image_path": image_path,
        "quantity": quantity,
        "work_title": work_title,
        "character_name": character_name,
        "description": description
    }).fetchone()["id"]

    db.execute(
        text("INSERT INTO item_categories (item_id, category_id) VALUES (:item_id, :category_id)"),
        {"item_id": item_id, "category_id": category_id}
    )

    db.commit()
    return jsonify({"status": "success"})


@items_bp.route('/items/<int:item_id>/edit', methods=['GET'])
def item_edit_form(item_id):
    db = SessionLocal()

    item_sql = text("SELECT * FROM items WHERE id = :item_id")
    item_row = db.execute(item_sql, {"item_id": item_id}).mappings().fetchone()
    if not item_row:
        return "Not Found", 404

    cat_sql = text("""
        SELECT categories.name
        FROM categories
        JOIN item_categories ON categories.id = item_categories.category_id
        WHERE item_categories.item_id = :item_id
    """)
    category_row = db.execute(cat_sql, {"item_id": item_id}).mappings().fetchone()
    category_name = category_row["name"] if category_row else ""

    categories = db.execute(text("SELECT * FROM categories")).fetchall()

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
    db = SessionLocal()
    user_id = session.get("user_id") or 1

    name = request.form.get("name")
    quantity = request.form.get("quantity", 0)
    work_title = request.form.get("work_title")
    character_name = request.form.get("character_name")
    description = request.form.get("description", "").strip() or None
    category = request.form.get("category")
    image_file = request.files.get("image_file")

    errors = []
    if not name:
        errors.append("グッズ名は必須です")
    if not category or category.strip() == "":
        errors.append("カテゴリーを選択してください")
    try:
        quantity = int(quantity)
        if quantity < 0:
            errors.append("個数は0以上で入力してください")
    except ValueError:
        errors.append("個数は数字で入力してください")
    if errors:
        return jsonify({"errors": errors}), 400

    old_item_sql = text("SELECT image_path FROM items WHERE id = :item_id AND user_id = :user_id")
    old_item = db.execute(old_item_sql, {"item_id": item_id, "user_id": user_id}).mappings().fetchone()
    if not old_item:
        return "Not Found", 404

    image_path = old_item["image_path"]

    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        upload_dir = os.path.join("static", "images")
        os.makedirs(upload_dir, exist_ok=True)
        image_file.save(os.path.join(upload_dir, filename))
        image_path = filename

    category_sql = text("SELECT id FROM categories WHERE name = :name")
    category_row = db.execute(category_sql, {"name": category}).mappings().fetchone()
    if category_row:
        category_id = category_row["id"]
    else:
        insert_cat_sql = text("INSERT INTO categories (name) VALUES (:name) RETURNING id")
        category_id = db.execute(insert_cat_sql, {"name": category}).fetchone()["id"]

    update_item_sql = text("""
        UPDATE items
        SET name = :name, image_path = :image_path, quantity = :quantity,
            work_title = :work_title, character_name = :character_name, description = :description
        WHERE id = :item_id AND user_id = :user_id
    """)
    db.execute(update_item_sql, {
        "name": name,
        "image_path": image_path,
        "quantity": quantity,
        "work_title": work_title,
        "character_name": character_name,
        "description": description,
        "item_id": item_id,
        "user_id": user_id
    })

    db.execute(text("DELETE FROM item_categories WHERE item_id = :item_id"), {"item_id": item_id})
    db.execute(
        text("INSERT INTO item_categories (item_id, category_id) VALUES (:item_id, :category_id)"),
        {"item_id": item_id, "category_id": category_id}
    )

    db.commit()
    return jsonify({"status": "success"})

@items_bp.route('/items/<int:item_id>/delete', methods=['POST'])
def item_delete(item_id):
    db = SessionLocal()
    user_id = session.get("user_id") or 1

    delete_sql = text("DELETE FROM items WHERE id = :item_id AND user_id = :user_id")
    db.execute(delete_sql, {"item_id": item_id, "user_id": user_id})
    db.commit()
    return jsonify({"status": "success"})

    
