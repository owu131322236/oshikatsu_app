from flask import Blueprint, render_template, request, redirect, session, jsonify
from db import get_db

items_bp = Blueprint('items', __name__)

@items_bp.route("/", methods=["GET"])
def item_search():
    db = get_db()
    sort = request.args.get("sort", "newest")

    if sort == "newest":
        order_by = "items.id DESC"
    elif sort == "num_items_desc":
        order_by = "items.quantity DESC"
    elif sort == "num_items_asc":
        order_by = "items.quantity ASC"
    else:
        order_by = "items.name DESC"

    # category_filter = request.args.getlist("category")
    categories = db.execute("SELECT name FROM categories").fetchall()

    item_rows = db.execute(
        f"""SELECT items.id, items.name, items.quantity, items.image_path, GROUP_CONCAT(categories.name) AS categories FROM items JOIN item_categories ON items.id = item_categories.item_id JOIN categories ON categories.id = item_categories.category_id GROUP BY items.id ORDER BY {order_by}"""
    ).fetchall()

    items=[]
    for item_row in item_rows:
        items.append({
            "id": item_row["id"],
            "name": item_row["name"],
            "quantity": item_row["quantity"],
            "image_path": item_row["image_path"],
            "categories": item_row["categories"].split(",") if item_row["categories"] else []
        })

    return render_template("index.html", items=items, categories=categories)

@items_bp.route("/items/<int:item_id>/modal", methods=["GET"])
def item_modal(item_id):
    db= get_db()
    item_row = db.execute(
        """SELECT items.id, items.name, items.description, items.quantity, items.image_path, items.work_title, items.character_name, GROUP_CONCAT(categories.name) AS categories FROM items JOIN item_categories ON items.id = item_categories.item_id JOIN categories ON categories.id = item_categories.category_id WHERE items.id = ? GROUP BY items.id""", (item_id,)).fetchone()
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
    