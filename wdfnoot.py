import streamlit as st
import requests
import base64
from typing import Optional, List, Dict, Any

# ---------------------- Secrets ----------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# ---------------------- Core Supabase Helpers ----------------------
def _headers(prefer: str = None) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def supabase_select(
    table: str,
    filter_col: str = None,
    filter_val: Any = None,
    order_col: str = None,
    desc: bool = False,
) -> List[dict]:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {}
    if filter_col is not None:
        params[filter_col] = f"eq.{filter_val}"
    if order_col:
        params["order"] = f"{order_col}.{'desc' if desc else 'asc'}"

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if resp.status_code >= 400:
            st.error(f"SELECT error {resp.status_code}: {resp.text}")
            return []
        return resp.json()
    except Exception as e:
        st.error(f"SELECT exception: {e}")
        return []


def supabase_insert(table: str, data: dict) -> Optional[List[dict]]:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        resp = requests.post(
            url, headers=_headers("return=representation"), json=data, timeout=15
        )
        if resp.status_code >= 400:
            st.error(f"INSERT error {resp.status_code}: {resp.text}")
            return None
        return resp.json()
    except Exception as e:
        st.error(f"INSERT exception: {e}")
        return None


def supabase_update(table: str, filter_col: str, filter_val: Any, data: dict) -> Optional[List[dict]]:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {filter_col: f"eq.{filter_val}"}
    try:
        resp = requests.patch(
            url, headers=_headers("return=representation"), params=params, json=data, timeout=10
        )
        if resp.status_code >= 400:
            st.error(f"UPDATE error {resp.status_code}: {resp.text}")
            return None
        return resp.json()
    except Exception as e:
        st.error(f"UPDATE exception: {e}")
        return None


def supabase_delete(table: str, filter_col: str, filter_val: Any) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {filter_col: f"eq.{filter_val}"}
    try:
        resp = requests.delete(url, headers=_headers(), params=params, timeout=10)
        if resp.status_code >= 400:
            st.error(f"DELETE error {resp.status_code}: {resp.text}")
            return False
        return True
    except Exception as e:
        st.error(f"DELETE exception: {e}")
        return False


# ---------------------- Notes API ----------------------
def add_note(title: str, content: str, tags: str = "") -> Optional[int]:
    data = {
        "title": title.strip(),
        "content": content,
        "tags": tags.strip(),
    }
    res = supabase_insert("notes", data)
    return res[0]["id"] if res else None


def get_all_notes() -> List[dict]:
    return supabase_select("notes", order_col="created_at", desc=True)


def get_note(note_id: int) -> Optional[dict]:
    res = supabase_select("notes", filter_col="id", filter_val=note_id)
    return res[0] if res else None


def update_note(note_id: int, title: str, content: str, tags: str = "") -> bool:
    data = {
        "title": title.strip(),
        "content": content,
        "tags": tags.strip(),
    }
    return supabase_update("notes", "id", note_id, data) is not None


def delete_note(note_id: int) -> bool:
    # Also delete related files first (optional but recommended)
    files = get_files(note_id)
    for f in files:
        delete_file(f["id"])
    return supabase_delete("notes", "id", note_id)


# ---------------------- Files API ----------------------
def add_file(note_id: int, file_name: str, file_type: str, file_bytes: bytes) -> Optional[int]:
    # Store as base64 string (Supabase JSON column)
    data = {
        "note_id": note_id,
        "file_name": file_name,
        "file_type": file_type or "application/octet-stream",
        "file_data": base64.b64encode(file_bytes).decode("utf-8"),
    }
    res = supabase_insert("files", data)
    return res[0]["id"] if res else None


def add_file_blob(note_id: int, uploaded_file) -> Optional[int]:
    """Helper for Streamlit UploadedFile objects"""
    return add_file(
        note_id=note_id,
        file_name=uploaded_file.name,
        file_type=uploaded_file.type,
        file_bytes=uploaded_file.getvalue(),
    )


def get_files(note_id: int) -> List[dict]:
    return supabase_select("files", filter_col="note_id", filter_val=note_id)


def delete_file(file_id: int) -> bool:
    return supabase_delete("files", "id", file_id)


# ---------------------- Search ----------------------
def search_notes(keyword: str) -> List[dict]:
    if not keyword.strip():
        return get_all_notes()

    url = f"{SUPABASE_URL}/rest/v1/notes"
    kw = keyword.replace("%", r"\%").replace(",", " ")
    params = {
        "or": f"(title.ilike.%{kw}%,content.ilike.%{kw}%)"
    }
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if resp.status_code >= 400:
            st.error(f"Search error: {resp.text}")
            return []
        return resp.json()
    except Exception as e:
        st.error(f"Search exception: {e}")
        return []


def search_by_title_exact(keyword: str) -> List[dict]:
    return supabase_select("notes", filter_col="title", filter_val=keyword)


# ---------------------- UI Helpers ----------------------
def render_file_preview(file_record: dict):
    """Simple file preview / download"""
    try:
        raw = base64.b64decode(file_record["file_data"])
    except Exception:
        st.warning("无法解码附件数据")
        return

    name = file_record["file_name"]
    mime = file_record.get("file_type", "application/octet-stream")

    st.download_button(
        label=f"⬇️ 下载 {name}",
        data=raw,
        file_name=name,
        mime=mime,
        key=f"dl_{file_record['id']}",
    )

    # Simple image preview
    if mime.startswith("image/"):
        st.image(raw, caption=name, use_container_width=True)


# ==================== Sidebar ====================
with st.sidebar:
    st.markdown("### 📝 本地智能笔记【云演示版】")
    st.caption("⚠️ 演示环境，数据仅保存在 Supabase")
    mode = st.radio(
        "功能模式",
        ["对话新增", "全局目录", "精准检索", "编辑管理"],
        index=0,
    )
    st.divider()
    total = len(get_all_notes())
    st.metric("笔记总数", total)


# ==================== Main ====================
st.markdown("## 本地智能笔记管理系统")
st.caption("对话式输入 · 自动目录 · 全文检索 · 文件绑定")

# ---------- 模式1：对话新增 ----------
if mode == "对话新增":
    st.subheader("💬 对话式新增笔记")
    with st.form("new_note_form", clear_on_submit=True):
        title = st.text_input("标题（必填）", placeholder="例如：术前谈话模板")
        content = st.text_area("正文内容（支持 Markdown）", height=220)
        tags = st.text_input("标签（可选，用逗号分隔）")
        uploaded_files = st.file_uploader("绑定附件（可多选）", accept_multiple_files=True)
        submitted = st.form_submit_button("保存笔记", type="primary", use_container_width=True)

        if submitted:
            if not title.strip() and not content.strip():
                st.error("标题和内容不能同时为空")
            else:
                if not title.strip():
                    title = content.strip().replace("\n", " ")[:30]
                note_id = add_note(title, content, tags)
                if note_id:
                    if uploaded_files:
                        for f in uploaded_files:
                            add_file_blob(note_id, f)
                    st.success(f"✅ 笔记已保存（ID: {note_id}）")
                    st.balloons()
                else:
                    st.error("保存失败")

# ---------- 模式2：全局目录 ----------
elif mode == "全局目录":
    st.subheader("📂 全局笔记目录")
    notes = get_all_notes()
    if not notes:
        st.info("暂无笔记，请先在「对话新增」中创建。")
    else:
        all_tags = set()
        for n in notes:
            if n.get("tags"):
                all_tags.update(t.strip() for t in n["tags"].split(",") if t.strip())

        selected_tag = st.selectbox("按标签筛选", ["全部"] + sorted(all_tags))

        for note in notes:
            tags = note.get("tags") or ""
            if selected_tag != "全部" and selected_tag not in [t.strip() for t in tags.split(",")]:
                continue

            with st.container(border=True):
                col1, col2 = st.columns([8, 2])
                with col1:
                    st.markdown(f"### {note['title']}")
                    st.caption(
                        f"创建: {note.get('created_at', '')} | "
                        f"更新: {note.get('updated_at', '')} | "
                        f"标签: {tags or '无'}"
                    )
                    preview = (note.get("content") or "")[:200]
                    st.markdown(preview + ("..." if len(note.get("content") or "") > 200 else ""))
                with col2:
                    if st.button("查看详情", key=f"view_{note['id']}"):
                        st.session_state["view_id"] = note["id"]

        if "view_id" in st.session_state:
            note = get_note(st.session_state["view_id"])
            if note:
                st.divider()
                st.subheader(f"📄 {note['title']}")
                st.caption(
                    f"创建: {note.get('created_at')} | 更新: {note.get('updated_at')} | "
                    f"标签: {note.get('tags') or '无'}"
                )
                st.markdown(note.get("content") or "_无正文_")

                files = get_files(note["id"])
                if files:
                    st.markdown("**附件：**")
                    for f in files:
                        with st.expander(f["file_name"]):
                            render_file_preview(f)

                if st.button("关闭详情"):
                    del st.session_state["view_id"]
                    st.rerun()

# ---------- 模式3：精准检索 ----------
elif mode == "精准检索":
    st.subheader("🔍 精准检索")
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("输入关键词", placeholder="支持模糊搜索")
    with col2:
        exact = st.checkbox("标题精确匹配")

    if keyword:
        results = search_by_title_exact(keyword) if exact else search_notes(keyword)
        st.write(f"找到 **{len(results)}** 条结果")
        for note in results:
            with st.expander(f"📌 {note['title']} （更新于 {note.get('updated_at', '')}）"):
                st.caption(f"标签: {note.get('tags') or '无'} | 创建: {note.get('created_at')}")
                st.markdown(note.get("content") or "_无正文_")
                files = get_files(note["id"])
                if files:
                    st.markdown("**附件：**")
                    for f in files:
                        render_file_preview(f)

# ---------- 模式4：编辑管理 ----------
elif mode == "编辑管理":
    st.subheader("✏️ 编辑 / 删除笔记")
    notes = get_all_notes()
    if not notes:
        st.info("暂无笔记")
    else:
        options = {f"{n['title']} (ID:{n['id']})": n["id"] for n in notes}
        selected = st.selectbox("选择要操作的笔记", list(options.keys()))
        note_id = options[selected]
        note_data = get_note(note_id)

        if note_data:
            title_edit = st.text_input("笔记标题", value=note_data["title"])
            content_edit = st.text_area("笔记内容", value=note_data.get("content") or "", height=250)
            tags_edit = st.text_input("标签", value=note_data.get("tags") or "")

            col_save, col_del = st.columns(2)
            with col_save:
                if st.button("💾 保存修改", type="primary"):
                    if update_note(note_id, title_edit, content_edit, tags_edit):
                        st.success("修改已保存")
                        st.rerun()
            with col_del:
                confirm_del = st.checkbox("确认永久删除本条笔记")
                if confirm_del and st.button("🗑️ 删除笔记", type="secondary"):
                    if delete_note(note_id):
                        st.success("笔记已删除")
                        st.rerun()

            st.divider()
            st.markdown("**当前附件**")
            files = get_files(note_id)
            if files:
                for f in files:
                    c1, c2, c3 = st.columns([5, 2, 2])
                    with c1:
                        st.write(f["file_name"])
                    with c2:
                        try:
                            raw = base64.b64decode(f["file_data"])
                            st.download_button(
                                "下载",
                                data=raw,
                                file_name=f["file_name"],
                                mime=f.get("file_type"),
                                key=f"dl_{f['id']}",
                            )
                        except Exception:
                            st.write("解码失败")
                    with c3:
                        if st.button("删除附件", key=f"del_{f['id']}"):
                            if delete_file(f["id"]):
                                st.rerun()
            else:
                st.write("暂无附件")

            st.markdown("**追加附件**")
            new_files = st.file_uploader("选择文件", accept_multiple_files=True, key="append_files")
            if new_files and st.button("上传附件"):
                for f in new_files:
                    add_file_blob(note_id, f)
                st.success("附件已添加")
                st.rerun()
