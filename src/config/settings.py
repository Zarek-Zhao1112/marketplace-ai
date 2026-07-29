"""
统一配置管理
所有环境变量、路径、常量集中管理
"""
import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# ── 项目根目录 ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── 数据文件路径 ────────────────────────────────────────────────
ISSUES_PATH = str(DATA_DIR / "issues.xlsx")
BRANDS_PATH = str(DATA_DIR / "brands.xlsx")
CONTACTS_PATH = str(DATA_DIR / "contacts.xlsx")
EXPERIENCE_PATH = str(DATA_DIR / "experience.json")
EMAILS_PATH = str(DATA_DIR / "emails.xlsx")

# ── 演示模式 ─────────────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")

# ── API 配置 ────────────────────────────────────────────────────
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
VOLC_REGION = os.getenv("VOLC_REGION", "cn-beijing")
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# ── 业务常量 ────────────────────────────────────────────────────
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

SCALE_MAP = {"初创": "初创品牌", "成长": "成长品牌", "成熟": "成熟品牌", "知名": "知名品牌"}

RMA_RULES = [
    (2.0, 20),   # ≤2% → 20分（与行业基准对齐）
    (5.0, 16),   # ≤5% → 16分
    (8.0, 12),   # ≤8% → 12分
    (15.0, 8),   # ≤15% → 8分
    (25.0, 4),   # ≤25% → 4分
    (float("inf"), 0),
]

GRADE_RULES = {
    "A": {"min": 75, "label": "核心优质卖家", "color": "#52c41a"},
    "B": {"min": 60, "label": "高潜力卖家", "color": "#1890ff"},
    "C": {"min": 45, "label": "普通合规卖家", "color": "#faad14"},
    "D": {"min": 0, "label": "高风险卖家", "color": "#f5222d"},
}

CATEGORY_OPTIONS = ["电竞外设", "电脑硬件", "手机数码", "家居用品", "美妆个护", "其他"]
SCALE_OPTIONS = ["初创品牌", "成长品牌", "成熟品牌", "知名品牌"]

CONTACT_PATHS = [
    "", "/contact", "/contact-us", "/about", "/about-us",
    "/contactus", "/contact_us", "/lianxi", "/lianxiwomen",
    "/zh/contact", "/about/contact",
]

INVALID_EMAIL_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

# ── 3C/消费电子 行业基准 ───────────────────────────────────────
INDUSTRY_BENCHMARKS = {
    "RMA%": {
        "label": "退货率(RMA%)",
        "excellent": {"threshold": 3, "label": "优秀(<3%)"},
        "good": {"threshold": 5, "label": "良好(3-5%)"},
        "average": {"threshold": 8, "label": "一般(5-8%)"},
        "poor": {"threshold": 100, "label": "较差(>8%)"},
    },
    "毛利率%": {
        "label": "毛利率",
        "excellent": {"threshold": 15, "label": "优秀(>15%)"},
        "good": {"threshold": 10, "label": "良好(10-15%)"},
        "average": {"threshold": 5, "label": "一般(5-10%)"},
        "poor": {"threshold": 0, "label": "较差(<5%)"},
    },
    "GMV": {
        "label": "月GMV($)",
        "excellent": {"threshold": 50000, "label": "优秀(>$50K)"},
        "good": {"threshold": 20000, "label": "良好($20-50K)"},
        "average": {"threshold": 5000, "label": "一般($5-20K)"},
        "poor": {"threshold": 0, "label": "较差(<$5K)"},
    },
    "SKU动销率%": {
        "label": "SKU动销率",
        "excellent": {"threshold": 80, "label": "优秀(>80%)"},
        "good": {"threshold": 60, "label": "良好(60-80%)"},
        "average": {"threshold": 40, "label": "一般(40-60%)"},
        "poor": {"threshold": 0, "label": "较差(<40%)"},
    },
    "库存周转": {
        "label": "库存周转(次/年)",
        "excellent": {"threshold": 8, "label": "优秀(>8次)"},
        "good": {"threshold": 5, "label": "良好(5-8次)"},
        "average": {"threshold": 3, "label": "一般(3-5次)"},
        "poor": {"threshold": 0, "label": "较差(<3次)"},
    },
}

INDUSTRY_GRADE_THRESHOLDS = {
    "A": 75,
    "B": 60,
    "C": 45,
    "D": 0,
}

NEWEGG_PITCHES = {
    "电竞外设": {
        "platform": "Newegg is the premier destination for gaming enthusiasts across North America, "
                     "home to a passionate community of gamers and eSports fans who actively seek out "
                     "the latest peripherals and gear.",
        "audience": "Our gaming audience is among the most purchase-ready in the industry — dedicated "
                     "players who invest seriously in their setups, actively leave reviews, and show "
                     "strong brand loyalty once a product earns their trust.",
        "category": "Gaming peripherals (keyboards, mice, headsets, controllers) consistently rank in "
                     "our top-performing categories, with high repeat-purchase rates and strong "
                     "community-driven discovery.",
        "support": "We offer dedicated gaming storefronts, featured placements in major gaming sales "
                     "events (Gamer Deals Fest, Shell Shocker), influencer co-marketing programs, and "
                     "a robust review ecosystem that drives authentic word-of-mouth.",
    },
    "电脑硬件": {
        "platform": "Newegg is North America's leading platform for PC builders and hardware "
                     "enthusiasts, trusted by a deeply knowledgeable community that relies on us for "
                     "the components powering their builds.",
        "audience": "Our customers are tech-savvy, research-intensive buyers with above-average order "
                     "values — they compare specs carefully and trust brands that invest in quality, "
                     "documentation, and community support.",
        "category": "PC hardware is our flagship category — CPUs, GPUs, storage, cooling, and "
                     "peripherals. Our platform drives substantial traffic from enthusiasts building "
                     "everything from entry-level rigs to high-end workstations.",
        "support": "We provide detailed spec listing tools, compatibility guides, combo-deal "
                     "promotions, direct integration with our PC Builder configurator, and "
                     "Newegg Business access for B2B and enterprise hardware procurement.",
    },
    "手机数码": {
        "platform": "Newegg serves a tech-forward North American audience that actively looks to us "
                     "for the latest mobile accessories, smart devices, and consumer electronics.",
        "audience": "Our customers are early adopters and informed buyers who value quality, "
                     "compatibility, and innovation — they're willing to pay a premium for products "
                     "that genuinely stand out.",
        "category": "Mobile accessories and smart devices are among our fastest-growing segments, "
                     "driven by strong demand for ecosystem accessories, wireless charging, audio, "
                     "and productivity gadgets.",
        "support": "We offer targeted promotional placements, bundle opportunities with "
                     "complementary tech products, strong SEO-driven category discovery, and "
                     "dedicated account support for mobile/digital brands.",
    },
    "家居用品": {
        "platform": "Newegg has significantly expanded its smart home and tech-forward home goods "
                     "category, attracting homeowners who want connected, innovative products backed "
                     "by a trusted tech retailer.",
        "audience": "Our home goods customers are tech-savvy homeowners blending functionality with "
                     "quality — they research before buying, value smart features, and leave "
                     "detailed, helpful reviews.",
        "category": "Smart home devices, home office equipment, and tech-enabled home products have "
                     "seen consistent growth on our platform, with strong cross-category purchasing "
                     "from our core technology audience.",
        "support": "We offer home and lifestyle promotional events, smart home bundle deals, "
                     "featured placements in our Home Tech collections, and cross-promotional "
                     "visibility alongside complementary tech products.",
    },
    "美妆个护": {
        "platform": "Newegg's expanding lifestyle and personal care category is reaching a growing "
                     "wave of tech-forward consumers who apply the same research mindset they use "
                     "for electronics to their personal care purchases.",
        "audience": "Our audience consists of well-informed, quality-conscious consumers who respond "
                     "strongly to brands with clear differentiation, innovation credentials, and "
                     "authentic reviews.",
        "category": "Personal care technology — skincare devices, advanced grooming tools, and "
                     "wellness tech — is one of our highest-growth emerging categories as our "
                     "audience continues to diversify.",
        "support": "We can feature your brand in our Lifestyle collections, leverage our trusted "
                     "review community for authentic product exposure, and run targeted promotional "
                     "campaigns to reach our expanding lifestyle consumer segment.",
    },
    "其他": {
        "platform": "Newegg is a trusted North American e-commerce platform serving over 40 million "
                     "registered customers across technology, electronics, and lifestyle categories.",
        "audience": "Our customer base consists of educated, purchase-ready shoppers who actively "
                     "seek quality products and rely on Newegg for competitive pricing, reliable "
                     "service, and authentic reviews.",
        "category": "We are actively expanding our product assortment to better serve our diverse "
                     "customer base, with strong support for emerging and established brands across "
                     "multiple categories.",
        "support": "We offer comprehensive seller support: optimized listing tools, promotional "
                     "campaign management, Newegg Business B2B access, and dedicated account "
                     "management for growing brands.",
    },
}

SCALE_VALUE_PROPS = {
    "初创品牌": (
        "Newegg's New Seller Program is specifically designed for emerging brands — "
        "with low barriers to entry, promotional launch support, and a highly engaged "
        "audience eager to discover the next standout product."
    ),
    "成长品牌": (
        "Newegg offers the scale and audience reach to accelerate your brand's next "
        "growth phase, with performance analytics, A/B testing tools, and targeted "
        "marketing programs to expand your North American presence."
    ),
    "成熟品牌": (
        "Adding Newegg to your channel mix gives your brand dedicated access to North "
        "America's most loyal tech buyer community, complementing your existing retail "
        "relationships with a high-intent digital audience."
    ),
    "知名品牌": (
        "Newegg's Premium Brand Program offers elevated storefronts, priority "
        "placements, and data-driven insights to help global brands maximize revenue "
        "from North America's most engaged technology consumer community."
    ),
}
