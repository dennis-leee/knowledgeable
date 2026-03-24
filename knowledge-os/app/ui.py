"""Streamlit Web UI for Knowledge OS."""

import asyncio
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Knowledge OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 Knowledge OS")
st.markdown("**AI 知识图谱自生长系统** - 自动从 URL 提取知识、构建图谱、生成 Skills")


def init_session_state():
    """Initialize session state."""
    if "results" not in st.session_state:
        st.session_state.results = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = ""


PIPELINE_STAGES = [
    ("ingestion", "📥 获取页面内容"),
    ("summarizer", "📝 生成摘要"),
    ("entity", "🏷️ 提取实体"),
    ("relation", "🔗 分析关系"),
    ("insight", "💡 提取洞察"),
    ("structuring", "🧩 构建知识结构"),
    ("validation", "✅ 质量验证"),
    ("repair", "🔧 修复问题"),
    ("memory", "💾 保存到知识库"),
    ("skills", "📦 生成 Skills"),
]

STAGE_DESCRIPTIONS = {
    "ingestion": "正在获取页面内容...",
    "summarizer": "正在生成摘要...",
    "entity": "正在提取实体...",
    "relation": "正在分析关系...",
    "insight": "正在提取洞察...",
    "structuring": "正在构建知识结构...",
    "validation": "正在进行质量验证...",
    "repair": "正在修复问题...",
    "memory": "正在保存到知识库...",
    "skills": "正在生成 Skills...",
}


async def run_pipeline(url: str, progress_callback=None):
    """Run the knowledge extraction pipeline."""
    from app.orchestrator import KnowledgePipeline

    pipeline = KnowledgePipeline()
    result = await pipeline.run(url, progress_callback=progress_callback)
    return result


def display_knowledge(result: dict):
    """Display knowledge extraction results."""
    if "error" in result and not result.get("raw_text"):
        st.error(f"错误: {result.get('error')}")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 摘要")
        summary = result.get("summary", "N/A")
        if len(summary) > 500:
            st.write(summary[:500] + "...")
        else:
            st.write(summary)

    with col2:
        st.subheader("📊 统计")
        st.metric("实体数量", len(result.get("entities", [])))
        st.metric("关系数量", len(result.get("relations", [])))
        st.metric("洞察数量", len(result.get("insights", [])))

    if result.get("entities"):
        st.subheader("🏷️ 实体")
        entities = result.get("entities", [])
        for entity in entities[:10]:
            if isinstance(entity, dict):
                st.write(f"- **{entity.get('name', 'N/A')}** ({entity.get('type', 'unknown')})")
            else:
                st.write(f"- **{entity.name}** ({entity.type})")

    if result.get("relations"):
        st.subheader("🔗 关系")
        relations = result.get("relations", [])
        for rel in relations[:5]:
            if isinstance(rel, dict):
                st.write(f"- {rel.get('source', '?')} --[{rel.get('type', 'related')}]--> {rel.get('target', '?')}")
            else:
                st.write(f"- {rel.source} --[{rel.type}]--> {rel.target}")

    if result.get("insights"):
        st.subheader("💡 洞察")
        insights = result.get("insights", [])
        for insight in insights[:5]:
            if isinstance(insight, dict):
                st.info(f"**{insight.get('insight_type', 'insight')}**: {insight.get('text', 'N/A')[:200]}")
            else:
                st.info(f"**{insight.insight_type}**: {insight.text[:200]}")

    if result.get("validated"):
        st.success("✅ 验证通过")
    else:
        st.warning("⚠️ 验证失败")
        if result.get("validation_errors"):
            st.write("错误:", result.get("validation_errors"))

    if result.get("skill_path"):
        st.success(f"📦 Skill 已生成: {result.get('skill_path')}")


def main():
    """Main Streamlit app."""
    init_session_state()

    st.sidebar.header("⚙️ 设置")

    with st.sidebar:
        st.subheader("📥 输入")
        url_input = st.text_input("URL", placeholder="https://example.com")

        col1, col2 = st.columns(2)
        with col1:
            run_button = st.button("🚀 开始处理", type="primary", disabled=st.session_state.processing)
        with col2:
            clear_button = st.button("🗑️ 清空")

        if clear_button:
            st.session_state.results = []
            st.rerun()

        st.divider()

        st.subheader("📁 历史记录")
        if st.session_state.results:
            for i, res in enumerate(st.session_state.results):
                with st.expander(f"Result {i+1}: {res.get('title', 'Untitled')[:30]}..."):
                    display_knowledge(res)
        else:
            st.info("暂无历史记录")

    st.divider()

    if run_button and url_input:
        st.session_state.processing = True
        progress_bar = st.progress(0, text="准备开始...")
        status_text = st.empty()
        stage_placeholder = st.empty()

        def progress_callback(stage: str, progress: int):
            status_text.text(STAGE_DESCRIPTIONS.get(stage, f"正在处理: {stage}..."))
            progress_bar.progress(progress)
            stage_names = [s[0] for s in PIPELINE_STAGES]
            if stage in stage_names:
                current_idx = stage_names.index(stage)
                completed = PIPELINE_STAGES[:current_idx]
                current = [(stage, STAGE_DESCRIPTIONS.get(stage, stage))]
                remaining = PIPELINE_STAGES[current_idx + 1:]
                stage_text = " → ".join([s[1] for s in completed]) + " → " + current[0][1] + " → " + " → ".join([s[1] for s in remaining])
                stage_placeholder.caption(stage_text)

        try:
            result = asyncio.run(run_pipeline(url_input, progress_callback=progress_callback))
            st.session_state.results.append(result)
            progress_bar.progress(100, text="处理完成!")
            st.rerun()
        except Exception as e:
            st.error(f"处理失败: {str(e)}")
        finally:
            st.session_state.processing = False

    if not st.session_state.results:
        st.info("👈 在侧边栏输入 URL 开始处理")


if __name__ == "__main__":
    main()
