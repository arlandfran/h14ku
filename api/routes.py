import random
from datetime import datetime
from bson import ObjectId
from flask import request
from flask_login import login_required

from app import mongo
from app.helpers import parse_json
from app.haikus import haikus
from api import api_bp


@api_bp.get("/posts")
def get_posts():
    post_filter = request.args.get("filter")
    if post_filter:
        if post_filter == "popular":
            posts = mongo.db.posts.find({}).sort("likes", -1).limit(10)
            data = parse_json(posts)
            return {"data": data}, 200
        if post_filter == "newest":
            posts = mongo.db.posts.find({}).sort("posted_at", -1).limit(10)
            data = parse_json(posts)
            return {"data": data}, 200
        if post_filter == "my-haikus":
            username = request.args.get("username")
            posts = (
                mongo.db.posts.find({"author": username})
                .sort("posted_at", -1)
                .limit(10)
            )
            data = parse_json(posts)
            return {"data": data}, 200
    return {"msg": "either no arguments given or the argument given is invalid"}, 400


@api_bp.get("/post")
def get_post():
    post_id = request.args.get("id")
    if post_id:
        document = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        data = parse_json(document)
        return {"data": data}, 200
    return {"msg": "no id given"}, 400


@api_bp.post("/post")
@login_required
def post():
    if request.args.get("id"):
        post_id = request.args.get("id")
        data = request.json
        document = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        if document:
            new_comment = {
                "username": data["username"],
                "comment": data["comment"],
                "posted_at": datetime.now(),
            }
            mongo.db.posts.update_one(
                {"_id": ObjectId(post_id)}, {"$push": {"comments": new_comment}}
            )
            return {"msg": "comment added"}, 200
        return {
            "msg": "either no arguments given or the argument given is invalid"
        }, 400
    if not request.args.get("id"):
        data = request.json
        document = {
            "author": data["author"],
            "haiku": data["haiku"],
            "posted_at": datetime.now(),
            "likes": 0,
            "comments": [],
            "edited": False,
        }
        mongo.db.posts.insert_one(document)
        return {"msg": "haiku posted successfully"}, 200  #
    return {"msg": "either no arguments given or the argument given is invalid"}


@api_bp.put("/post")
@login_required
def update_post():
    post_id = request.args.get("id")
    data = request.json
    document = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if document:
        mongo.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"haiku": data["haiku"], "edited": True}},
        )
        return {"msg": "haiku updated successfully"}, 200
    return {"msg": "either no arguments given or the argument given is invalid"}, 400


@api_bp.patch("/post")
@login_required
def like_post():
    post_id = request.args.get("id")
    like = request.args.get("like")
    username = request.json["username"]
    if like == "true":
        mongo.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"likes": username}},
        )
        return {"liked": True}, 200
    if like == "false":
        mongo.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": username}},
        )
        return {"liked": False}, 200
    return {"msg": "either no arguments given or the argument given is invalid"}, 400


@api_bp.delete("/post")
@login_required
def delete_post():
    post_id = request.args.get("id")
    document = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if document:
        mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
        return {"msg": "haiku deleted successfully"}, 200
    return {"msg": "either no arguments given or the argument given is invalid"}, 400


@api_bp.get("/user")
def get_user():
    username = request.args.get("username")
    if username:
        user = mongo.db.users.find_one({"username": username})
        if user:
            posts = (
                mongo.db.posts.find({"author": username})
                .sort("posted_at", -1)
                .limit(10)
            )
            if not posts:
                return {"data": []}, 200
            data = parse_json(posts)
            return {"data": data}, 200
        return {"msg": "username not found"}, 404
    return {"msg": "no username given"}, 400


@api_bp.get("/haiku")
def get_haiku():
    haiku = random.choice(haikus)
    return {"data": haiku}, 200
