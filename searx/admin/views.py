from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # placeholder - real check via auth.decorators
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")

@admin_bp.route("/users")
@admin_required
def users_list():
    from searx.auth.models import UserStore
    store = UserStore()
    users = store.list_users()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def user_create():
    from searx.auth.models import UserStore, Role
    if request.method == "POST":
        store = UserStore()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = Role(int(request.form.get("role", 10)))
        display_name = request.form.get("display_name", "").strip()
        if not username or not password:
            flash("Username and password required", "error")
        else:
            try:
                store.create_user(username, password, role=role, display_name=display_name)
                flash("User created", "success")
                return redirect(url_for("admin.users_list"))
            except Exception as e:
                flash(str(e), "error")
    return render_template("admin/user_form.html", user=None, roles=[(r.value, r.name) for r in Role])

@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def user_edit(user_id):
    from searx.auth.models import UserStore, Role
    store = UserStore()
    user = store.get_user(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("admin.users_list"))
    if request.method == "POST":
        kwargs = {
            "display_name": request.form.get("display_name", "").strip(),
            "role": Role(int(request.form.get("role", 10))),
            "is_active": request.form.get("is_active") == "on",
        }
        if request.form.get("password"):
            kwargs["password"] = request.form.get("password")
        store.update_user(user_id, **kwargs)
        flash("User updated", "success")
        return redirect(url_for("admin.users_list"))
    return render_template("admin/user_form.html", user=user, roles=[(r.value, r.name) for r in Role])

@admin_bp.route("/engines")
@admin_required
def engines():
    return render_template("admin/engines.html")

@admin_bp.route("/widgets")
@admin_required
def widgets():
    return render_template("admin/widgets.html")

@admin_bp.route("/plugins")
@admin_required
def plugins():
    return render_template("admin/plugins.html")

@admin_bp.route("/settings")
@admin_required
def settings():
    return render_template("admin/settings.html")
