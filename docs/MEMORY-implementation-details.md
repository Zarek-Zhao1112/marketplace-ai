# Implementation details (spillover from MEMORY.md)
_Stable patterns, completed historical items, and general tips extracted from main MEMORY.md to stay under token budget._

## Streamlit patterns
- **Streamlit `use_container_width` deprecation (2026-06-29)**: All `use_container_width=True` must become `width="stretch"`, `use_container_width=False` → `width="content"`. Applies to `st.plotly_chart`, `st.dataframe`, `st.data_editor`, `st.button`. Deprecated after Streamlit 1.58.0, removal target 2025-12-31.
- **File pointer exhaustion with Streamlit UploadedFile**: `st.file_uploader` returns BytesIO-like objects. Every `pd.read_excel(uploaded_file)` consumes the entire file, leaving pointer at EOF. Must call `uploaded_file.seek(0)` before ANY subsequent read on the same object.
- **Python function ordering in Streamlit pages**: Each page file is executed top-to-bottom on every rerun. Functions MUST be defined before call sites.
- **`st.date_input` returns `datetime.date`, not `datetime.datetime`**: All `.date()` calls on date variables must check `hasattr(d, 'date')` first.

## Python conventions
- **Coding standards**: 单文件上限300行, 函数上限50行, 类上限200行. 文件名snake_case, 类名PascalCase, 函数名snake_case, 常量UPPER_SNAKE, 私有方法_前缀. 按标准库→第三方→本地分组import. 禁止裸except、硬编码路径、硬编码API Key. 捕获具体异常. 用session_state管理状态, 不用全局变量.

## Data architecture (updated 2026-07-21)
- **Data files**: All in `data/` directory. `data/experience.json` is rebuilt from `issues.xlsx` when user clicks "重建经验库".
- **File-aware caching**: `data.py` uses `_cached_read_json()` based on file mtime. Cache auto-invalidates when files are deleted/modified.
- **Export filename format**: `{seller_id}_{起始日期}-{结束日期}.xlsx`
- **start.bat路径**: `C:\Users\zz79\marketplace-ai\start.bat`，端口8502。PowerShell不支持 `&&`，用 `;` 分隔命令。

## Code structure (updated 2026-07-21)
- **utils.py split**: Original 955-line utils.py was split into:
  - `utils.py` (74行): Excel I/O + text tools + UI helpers
  - `excel_export.py` (809行): All openpyxl formatting + charts
  - `web_scraper.py` (66行): Web scraping (requests + Playwright)
- **config.py shim removed**: `src/web/config.py` was a pure re-export (`from src.config.settings import *`). Deleted; all imports updated to `src.config.settings`.
- **AI parsing unified**: `_parse_chat_with_ai()` + `_parse_chat_with_images()` merged into single `_parse_chat()` with retry, JSON容错, 10min cache.
- **Knowledge base**: `newegg_seller_academy.py` contains 17 structured modules from Newegg Seller Academy website.

## Historical/completed items
- **`app.py` and `main.py` are identical**: Both serve as dashboard landing page. `app.py` is the legacy name.
- **SELLER_HISTORY_DIR路径（已废弃）**: `src/web/data.py`中 `SELLER_HISTORY_DIR = data/seller_history`。2026-07-01合并到 `sku_analysis/`，此目录不再写入新数据。
- **Page rename scheme (2026-06-29)**: `pages/2_运营笔记.py` → `pages/2_问题管理.py`, `pages/3_品牌线索库.py` → `pages/3_品牌线索.py`
- **Dead code removed (2026-07-21)**: `_db_inspect.py` (debug script), `src/web/config.py` (re-export shim), `experience_library.py` `suggest_reply()` (dead CLI code), `volcengine-python-sdk[ark]` from requirements.txt, 10 empty competitor JSON files.
