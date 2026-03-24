"""Streamlit Web UI for Knowledge OS - Full Agent Visualization."""

import asyncio
import streamlit as st
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Knowledge OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 Knowledge OS")
st.markdown("**AI 知识图谱自生长系统** - 从 URL 或文本中提取知识")


def init_session_state():
    """Initialize session state."""
    if "results" not in st.session_state:
        st.session_state.results = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "logs" not in st.session_state:
        st.session_state.logs = []
    if "agent_models" not in st.session_state:
        st.session_state.agent_models = {
            "summarizer": "openrouter/free",
            "entity": "openrouter/free",
            "relation": "openrouter/free",
            "insight": "openrouter/free",
            "skills": "openrouter/free",
        }
        st.session_state.agent_models = {
            "summarizer": "openrouter/free",
            "entity": "openrouter/free",
            "relation": "openrouter/free",
            "insight": "openrouter/free",
            "skills": "openrouter/free",
        }


def get_openrouter_free_models():
    """Fetch free models from OpenRouter."""
    try:
        import httpx
        api_key = st.session_state.get("openrouter_api_key", "")
        if not api_key:
            return ["openrouter/free"]
        
        headers = {"Authorization": f"Bearer {api_key}"}
        response = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            free_models = [
                m["id"] for m in data.get("data", [])
                if ":free" in m.get("id", "") or m.get("id", "").startswith("openrouter/")
            ]
            if not free_models:
                free_models = ["openrouter/free"]
            return ["openrouter/free"] + sorted(free_models)
    except Exception:
        pass
    return ["openrouter/free"]


AGENTS = [
    {"id": "ingestion", "name": "📥 内容获取", "model": "direct", "description": "从 URL 提取内容或直接接收文本"},
    {"id": "summarizer", "name": "📝 摘要生成", "model": "openrouter/free", "description": "生成内容摘要"},
    {"id": "entity", "name": "🏷️ 实体提取", "model": "openrouter/free", "description": "识别人名、地点、概念等实体"},
    {"id": "relation", "name": "🔗 关系分析", "model": "openrouter/free", "description": "分析实体之间的关系"},
    {"id": "insight", "name": "💡 洞察提取", "model": "openrouter/free", "description": "挖掘深层含义和洞察"},
    {"id": "structuring", "name": "🧩 知识组装", "model": "direct", "description": "构建知识结构"},
    {"id": "validation", "name": "✅ 质量验证", "model": "direct", "description": "验证知识质量"},
    {"id": "memory", "name": "💾 存储", "model": "direct", "description": "保存到知识库"},
    {"id": "skills", "name": "📦 Skills 生成", "model": "openrouter/free", "description": "生成 AI Agent 可用的 Skills"},
]


async def run_pipeline(url: str = None, text: str = None, progress_callback=None, stream_callback=None, agent_models=None):
    """Run the simplified pipeline."""
    from app.orchestrator.simple_pipeline import SimplePipeline

    pipeline = SimplePipeline()
    result = await pipeline.run(
        url=url, text=text,
        progress_callback=progress_callback,
        stream_callback=stream_callback,
        agent_models=agent_models
    )
    return result


def display_result(result: dict):
    """Display knowledge extraction results."""
    if "error" in result and not result.get("raw_text"):
        st.error(f"错误: {result.get('error')}")
        return

    st.markdown("---")
    st.markdown("## 📝 提取结果")

    summary = result.get("summary", "")
    if summary:
        st.markdown("### 摘要")
        st.markdown(summary)

    key_points = result.get("key_points", [])
    if key_points:
        st.markdown(f"### 💡 核心要点 ({len(key_points)} 条)")
        for i, point in enumerate(key_points, 1):
            if isinstance(point, dict):
                st.markdown(f"**{i}. {point.get('point', '')}**")
                explanation = point.get('explanation', '')
                example = point.get('example', '')
                if explanation:
                    st.caption(f"   📝 {explanation}")
                if example:
                    st.caption(f"   🔍 例如: {example}")
            else:
                st.markdown(f"**{i}. {point}**")

    important_details = result.get("important_details", [])
    if important_details:
        st.markdown(f"### 📌 重要细节 ({len(important_details)} 条)")
        for detail in important_details:
            st.markdown(f"- {detail}")

    takeaways = result.get("takeaways", [])
    if takeaways:
        st.markdown(f"### 🎯 关键收获 ({len(takeaways)} 条)")
        for takeaway in takeaways:
            st.success(f"💡 {takeaway}")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("实体", len(result.get("entities", [])))
    with col2:
        st.metric("关系", len(result.get("relations", [])))
    with col3:
        st.metric("洞察", len(result.get("insights", [])))
    with col4:
        st.metric("验证", "✅ 通过" if result.get("validated") else "⚠️ 未通过")

    if result.get("entities"):
        with st.expander("🏷️ 实体列表"):
            for entity in result.get("entities", [])[:15]:
                if isinstance(entity, dict):
                    st.write(f"- **{entity.get('name', 'N/A')}** ({entity.get('type', 'unknown')})")
                else:
                    st.write(f"- **{entity.name}** ({entity.type})")

    if result.get("relations"):
        with st.expander("🔗 关系列表"):
            for rel in result.get("relations", [])[:10]:
                if isinstance(rel, dict):
                    st.write(f"- {rel.get('source', '?')} --[{rel.get('type', 'related')}]--> {rel.get('target', '?')}")
                else:
                    st.write(f"- {rel.source} --[{rel.type}]--> {rel.target}")

    if result.get("insights"):
        with st.expander("💡 洞察列表"):
            for insight in result.get("insights", [])[:5]:
                if isinstance(insight, dict):
                    st.info(f"**{insight.get('insight_type', 'insight')}**: {insight.get('text', 'N/A')[:200]}")
                else:
                    st.info(f"**{insight.insight_type}**: {insight.text[:200]}")

    if result.get("skill_path"):
        st.success(f"📦 Skills 已生成: {result.get('skill_path')}")


def render_agent_card(agent: dict, status: str, progress: int, message: str = "", model_options: list = None, current_model: str = "openrouter/free", on_model_change=None):
    """Render a single agent card with model selector."""
    status_colors = {
        "pending": "gray",
        "running": "blue",
        "completed": "green",
        "error": "red",
    }
    status_icons = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "error": "❌",
    }

    color = status_colors.get(status, "gray")
    icon = status_icons.get(status, "⏳")

    is_llm_agent = agent["model"] != "direct"

    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{icon} {agent['name']}**")
            if message:
                st.text(message[:100] + ("..." if len(message) > 100 else ""))
        with col2:
            if status == "running":
                st.progress(progress, text=f"{progress}%")
            else:
                st.markdown(f"<span style='color:{color}'>{status.upper()}</span>", unsafe_allow_html=True)

        if is_llm_agent and model_options:
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_model = st.selectbox(
                    f"模型 ({agent['name']})",
                    options=model_options,
                    index=model_options.index(current_model) if current_model in model_options else 0,
                    key=f"model_{agent['id']}",
                    label_visibility="collapsed"
                )
            with col2:
                st.write("") 
                if st.button("🔄", key=f"refresh_{agent['id']}", help="刷新模型列表"):
                    st.rerun()

        st.divider()


def main():
    """Main Streamlit app."""
    init_session_state()

    st.sidebar.header("⚙️ 设置")

    with st.sidebar:
        from app.utils.llm import set_openrouter_api_key

        st.subheader("🔑 OpenRouter API Key")
        api_key_input = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.get("openrouter_api_key", ""),
            help="用于获取免费模型列表"
        )
        if api_key_input != st.session_state.get("openrouter_api_key", ""):
            st.session_state["openrouter_api_key"] = api_key_input
            if api_key_input:
                set_openrouter_api_key(api_key_input)

        st.divider()

        with st.expander("📋 Agent 列表", expanded=False):
            for agent in AGENTS:
                st.write(f"**{agent['name']}** - {agent['description']}")
                st.divider()

        st.divider()

        input_mode = st.radio(
            "输入方式",
            ["🌐 URL", "📋 粘贴文本"],
            captions=["从网页提取内容", "直接粘贴文章内容"]
        )

        if input_mode == "🌐 URL":
            url_input = st.text_input("URL", placeholder="https://example.com")
            text_input = None
        else:
            url_input = None
            text_input = st.text_area(
                "文章内容",
                placeholder="在此粘贴文章全文...",
                height=150
            )

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            run_button = st.button("🚀 开始处理", type="primary", disabled=st.session_state.processing)
        with col2:
            clear_button = st.button("🗑️ 清空")

        if clear_button:
            st.session_state.results = []
            st.session_state.logs = []
            st.rerun()

    st.markdown("## 🔄 Agent 工作流程")

    model_options = get_openrouter_free_models()

    agent_status = {agent["id"]: "pending" for agent in AGENTS}
    agent_progress = {agent["id"]: 0 for agent in AGENTS}
    agent_messages = {agent["id"]: "" for agent in AGENTS}

    if "agent_states" in st.session_state:
        for agent_id, state_data in st.session_state.agent_states.items():
            agent_status[agent_id] = state_data.get("status", "pending")
            agent_progress[agent_id] = state_data.get("progress", 0)
            agent_messages[agent_id] = state_data.get("message", "")

    for agent in AGENTS:
        current_model = st.session_state.agent_models.get(agent["id"], "openrouter/free")
        render_agent_card(
            agent,
            agent_status[agent["id"]],
            agent_progress[agent["id"]],
            agent_messages[agent["id"]],
            model_options=model_options,
            current_model=current_model
        )

        if agent["model"] != "direct":
            new_model = st.session_state.get(f"model_{agent['id']}", current_model)
            if new_model != current_model:
                st.session_state.agent_models[agent["id"]] = new_model

    st.markdown("---")

    st.markdown("## 📤 处理日志")
    log_placeholder = st.empty()

    if st.session_state.logs:
        log_text = "".join(st.session_state.logs)
        log_placeholder.text_area("日志", log_text, height=120, disabled=True, label_visibility="collapsed")
    else:
        log_placeholder.info("等待开始处理...")

    if run_button:
        if input_mode == "🌐 URL" and not url_input:
            st.warning("请输入 URL")
            return
        if input_mode == "📋 粘贴文本" and not text_input:
            st.warning("请输入文章内容")
            return

        st.session_state.processing = True
        st.session_state.logs = []
        st.session_state.agent_states = {}

        async def progress_handler(stage: str, progress: int, message: str):
            st.session_state.agent_states[stage] = {
                "status": "running",
                "progress": progress,
                "message": message
            }
            st.session_state.logs.append(f"[{progress}%] {message}\n")

        async def stream_handler(stage: str, content: str):
            if stage in st.session_state.agent_states:
                st.session_state.agent_states[stage]["message"] = content
            st.session_state.logs.append(f"[{stage}] {content}")

        try:
            result = asyncio.run(run_pipeline(
                url=url_input if input_mode == "🌐 URL" else None,
                text=text_input if input_mode == "📋 粘贴文本" else None,
                progress_callback=progress_handler,
                stream_callback=stream_handler,
                agent_models=st.session_state.agent_models
            ))

            for agent_id in agent_status:
                if agent_id in st.session_state.agent_states:
                    st.session_state.agent_states[agent_id]["status"] = "completed"
                    st.session_state.agent_states[agent_id]["progress"] = 100

            st.session_state.results.append(result)
            st.rerun()

        except Exception as e:
            st.error(f"处理失败: {str(e)}")
            if "current_agent" in st.session_state:
                st.session_state.agent_states[st.session_state.current_agent] = {"status": "error", "progress": 0, "message": str(e)}
        finally:
            st.session_state.processing = False

    if st.session_state.results:
        st.markdown("---")
        display_result(st.session_state.results[-1])

    if not st.session_state.results and not st.session_state.processing:
        st.info("👈 在侧边栏输入内容开始处理")


if __name__ == "__main__":
    main()
