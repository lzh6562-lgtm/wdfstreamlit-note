import streamlit as st
import requests
import json

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}

# ---------------------- 封装函数 ----------------------
def supabase_select(table_name: str, eq_col: str = None, eq_val=None, order_col: str = None, desc: bool = False):
    """查询
    eq_col、eq_val：等于筛选
    order_col：排序字段
    desc：是否倒序
    """
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    params = {}
    if eq_col is not None:
        params[eq_col] = f"eq.{eq_val}"
    if order_col is not None:
        if desc:
            params["order"] = f"{order_col}.desc"
        else:
            params["order"] = f"{order_col}.asc"
    resp = requests.get(url, headers=HEADERS, params=params)
    return resp.json()

def supabase_insert(table_name: str, data: dict):
    """新增一行，data是字典，对应表里字段"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    resp = requests.post(url, headers=HEADERS, data=json.dumps(data))
    return resp.json()

def supabase_update(table_name: str, match_col: str, match_val, update_data: dict):
    """更新：match_col=匹配条件字段，update_data要修改的字段字典"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    params = {match_col: f"eq.{match_val}"}
    resp = requests.patch(url, headers=HEADERS, params=params, data=json.dumps(update_data))
    return resp.json()

def supabase_delete(table_name: str, match_col: str, match_val):
    """删除一行"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    params = {match_col: f"eq.{match_val}"}
    resp = requests.delete(url, headers=HEADERS, params=params)
    return resp.json()

# 新增笔记
def add_note(title: str, content: str, tags: str = ""):
    data = {
        "title": title.strip(),
        "content": content,
        "tags": tags.strip(),
        "created_at": datetime.now().isoformat()
    }
    res_data = supabase_insert("notes", data)
    return res_data[0]["id"] if res_data else None

# 查询全部笔记
def get_notes():
    note_list = supabase_select("notes", order_col="created_at", desc=True)
    return note_list

# 修改笔记
def update_note(note_id: int, title: str, content: str, tags: str = ""):
    data = {
        "title": title.strip(),
        "content": content,
        "tags": tags.strip()
    }
    supabase_update("notes", "id", note_id, data)

# 删除笔记
def delete_note(note_id: int):
    return supabase_delete("notes", "id", note_id)

def add_note(title: str, content: str, tags: str = ""):
    data = {
        "title": title.strip(),
        "content": content,
        "tags": tags.strip()
    }
    res_data = supabase_insert("notes", data)
    return res_data[0]["id"] if res_data else None

def get_all_notes():
    res_data = supabase_select("notes", order_col="created_at", desc=True)
    return res_data

def get_note(note_id: int):
    res_data = supabase_select("notes", eq_col="id", eq_val=note_id)
    return res_data[0] if res_data else None

def update_note(note_id: int, title: str, content: str, tags: str = ""):
    data = {
        "title": title.strip(),
        "content": content,
        "tags": tags.strip()
    }
    supabase_update("notes", "id", note_id, data)

def delete_note(note_id: int):
    supabase_delete("notes", "id", note_id)

# ==================== 工具函数 ====================
def get_blob_download_link(file_bytes: bytes, filename: str) -> str:
    b64 = base64.b64encode(file_bytes).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">下载 {filename}</a>'

def render_file_preview(file_bytes: bytes, filename: str, filetype: str):
    ext = os.path.splitext(filename)[-1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
        st.image(file_bytes, caption=filename, use_container_width=True)
    elif ext == ".pdf":
        st.info(f"PDF 文件: {filename}（下载后本地打开）")
        st.markdown(get_blob_download_link(file_bytes, filename), unsafe_allow_html=True)
    elif ext in [".txt", ".md", ".py", ".json", ".csv"]:
        try:
            content = file_bytes.decode("utf-8", errors="ignore")
            st.code(content[:5000] + ("..." if len(content) > 5000 else ""), language="text")
        except Exception:
            st.warning("无法预览文本")
    else:
        st.info(f"附件: {filename}")
        st.markdown(get_blob_download_link(file_bytes, filename), unsafe_allow_html=True)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="本地智能笔记【云演示版】",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .stApp {
        background-color: #f7f9fc;
    }
    .main-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    .note-card {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        border: 1px solid #e1e8ed;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .note-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a365d;
        margin-bottom: 0.3rem;
    }
    .note-meta {
        font-size: 0.8rem;
        color: #718096;
        margin-bottom: 0.5rem;
    }
    .tag {
        background: #ebf8ff;
        color: #2b6cb0;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 4px;
    }
    div[data-testid="stSidebar"] {
        background-color: #edf2f7;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### 📝 本地智能笔记【云演示版】")
    st.caption("⚠️ 演示环境，刷新数据全部丢失")
    mode = st.radio(
        "功能模式",
        ["对话新增", "全局目录", "精准检索", "编辑管理"],
        index=0
    )
    st.divider()
    total = len(get_all_notes())
    st.metric("笔记总数", total)

# ==================== 主界面 ====================
st.markdown('<div class="main-header">本地智能笔记管理系统</div>', unsafe_allow_html=True)
st.caption("对话式输入 · 自动目录 · 全文检索 · 文件绑定 | ⚠️云演示，不持久存储")

# ---------- 模式1：对话新增 ----------
if mode == "对话新增":
    st.subheader("💬 对话式新增笔记")
    with st.form("new_note_form", clear_on_submit=True):
        title = st.text_input("标题（必填）", placeholder="例如：术前谈话模板 / 高血压用药提示")
        content = st.text_area("正文内容（支持 Markdown）", height=220,
                               placeholder="在此输入笔记内容...\n\n支持 **加粗**、*斜体*、列表、代码块等 Markdown 语法")
        tags = st.text_input("标签（可选，用逗号分隔）", placeholder="例如：模板,术前,外科 或 学习,心血管")
        uploaded_files = st.file_uploader("绑定附件（可多选，任意格式）",
                                          accept_multiple_files=True,
                                          type=None)
        submitted = st.form_submit_button("保存笔记", type="primary", use_container_width=True)
        if submitted:
            if not title.strip():
                if not content.strip():
                    st.error("标题和内容不能同时为空")
                else:
                    title = content.strip().replace('\n', ' ').replace('\r', '')[:20]
            if title.strip():
                note_id = add_note(title, content, tags)
                if uploaded_files:
                    for f in uploaded_files:
                        add_file_blob(note_id, f)
                st.success(f"✅ 笔记已保存（ID: {note_id}）")
                st.balloons()

# ---------- 模式2：全局目录 ----------
elif mode == "全局目录":
    st.subheader("📂 全局笔记目录")
    notes = get_all_notes()
    if not notes:
        st.info("暂无笔记，请先在「对话新增」中创建。")
    else:
        all_tags = set()
        for n in notes:
            if n[3]:
                for t in n[3].split(","):
                    all_tags.add(t.strip())
        selected_tag = st.selectbox("按标签筛选（可选）", ["全部"] + sorted(list(all_tags)))
        for note in notes:
            note_id, title, content, tags, created, updated = note
            if selected_tag != "全部" and (not tags or selected_tag not in [t.strip() for t in tags.split(",")]):
                continue
            with st.container():
                st.markdown(f'<div class="note-card">', unsafe_allow_html=True)
                col1, col2 = st.columns([8, 2])
                with col1:
                    st.markdown(f'<div class="note-title">{title}</div>', unsafe_allow_html=True)
                    tag_html = ""
                    if tags:
                        for t in tags.split(","):
                            tag_html += f'<span class="tag">{t.strip()}</span>'
                    st.markdown(f'<div class="note-meta">创建: {created} | 更新: {updated} {tag_html}</div>', unsafe_allow_html=True)
                    preview = content[:180] + "..." if len(content) > 180 else content
                    st.markdown(preview)
                    files = get_files(note_id)
                    if files:
                        st.caption(f"📎 附件 {len(files)} 个")
                with col2:
                    if st.button("查看详情", key=f"view_{note_id}"):
                        st.session_state["view_id"] = note_id
                st.markdown('</div>', unsafe_allow_html=True)
        if "view_id" in st.session_state:
            note = get_note(st.session_state["view_id"])
            if note:
                st.divider()
                st.subheader(f"📄 {note[1]}")
                st.caption(f"创建: {note[4]} | 更新: {note[5]} | 标签: {note[3] or '无'}")
                st.markdown(note[2] or "_无正文_")
                files = get_files(note[0])
                if files:
                    st.markdown("**附件：**")
                    for fid, fname, fbytes, ftype, _ in files:
                        with st.expander(fname):
                            render_file_preview(fbytes, fname, ftype)
                if st.button("关闭详情"):
                    del st.session_state["view_id"]
                    st.rerun()

# ---------- 模式3：精准检索 ----------
elif mode == "精准检索":
    st.subheader("🔍 精准检索")
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("输入标题关键词或正文关键词", placeholder="支持模糊搜索，回车即可")
    with col2:
        exact = st.checkbox("标题精确匹配", value=False)
    if keyword:
        if exact:
            results = search_by_title_exact(keyword)
        else:
            results = search_notes(keyword)
        st.write(f"找到 **{len(results)}** 条结果")
        for note in results:
            note_id, title, content, tags, created, updated = note
            with st.expander(f"📌 {title} （更新于 {updated}）"):
                st.caption(f"标签: {tags or '无'} | 创建: {created}")
                st.markdown(content or "_无正文_")
                files = get_files(note_id)
                if files:
                    st.markdown("**附件：**")
                    for fid, fname, fbytes, ftype, _ in files:
                        render_file_preview(fbytes, fname, ftype)

# ---------- 模式4：编辑管理 ----------
elif mode == "编辑管理":
    st.subheader("✏️ 编辑 / 删除笔记")
    notes = get_all_notes()
    if not notes:
        st.info("暂无笔记")
    else:
        options = {f"{n[1]} (ID:{n[0]})": n[0] for n in notes}
        selected = st.selectbox("选择要操作的笔记", list(options.keys()))
        note_id = options[selected]
        note = get_note(note_id)
        if note:
            with st.form("edit_form"):
                new_title = st.text_input("标题", value=note[1])
                new_content = st.text_area("内容", value=note[2] or "", height=250)
                new_tags = st.text_input("标签", value=note[3] or "")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("保存修改", type="primary"):
                        update_note(note_id, new_title, new_content, new_tags)
                        st.success("已更新")
                        st.rerun()
                with col_b:
                    if st.form_submit_button("删除此笔记", type="secondary"):
                        delete_note(note_id)
                        st.success("已删除")
                        st.rerun()
            st.markdown("**当前附件**")
            files = get_files(note_id)
            if files:
                for fid, fname, fbytes, ftype, uptime in files:
                    c1, c2 = st.columns([6, 1])
                    with c1:
                        st.download_button(
                            label=f"📎 {fname} ({uptime}) - 点击查看/下载",
                            data=fbytes,
                            file_name=fname,
                            key=f"dl_{fid}"
                        )
                    with c2:
                        if st.button("删除", key=f"del_f_{fid}"):
                            delete_file(fid)
                            st.rerun()
            else:
                st.caption("无附件")
            st.markdown("**追加附件**")
            new_files = st.file_uploader("选择文件", accept_multiple_files=True, key="append_files")
            if new_files and st.button("上传附件"):
                for f in new_files:
                    add_file_blob(note_id, f)
                st.success("附件已添加")
                st.rerun()

st.divider()
st.caption("⚠️云演示环境，刷新/重启全部数据丢失；本地运行原版代码可以永久保存在电脑磁盘")
