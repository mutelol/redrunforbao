from __future__ import annotations

import re

from .models import CandidateItem
from .utils import collapse_spaces, unique_preserve_order

TRANSLATIONS = [
    ("Hello Kitty", "Hello Kitty"),
    ("NEW", "新款"),
    ("ハローキティ", "Hello Kitty"),
    ("着ぐるみマスコットチャーム", "玩偶挂件"),
    ("メッシュバッグ", "网眼包"),
    ("バッグ", "包包"),
    ("ポーチ", "收纳包"),
    ("パスケース", "卡套"),
    ("チャーム", "挂件"),
    ("マスコット", "玩偶"),
    ("ファブリック", "布料"),
    ("fabric", "布料"),
    ("刺繍", "刺绣"),
    ("リボン", "蝴蝶结"),
    ("いちご", "草莓"),
    ("チェリー", "樱桃"),
    ("パイナップル", "菠萝"),
    ("ピンク", "粉色"),
    ("ブルー", "蓝色"),
    ("ホワイト", "白色"),
    ("ブラック", "黑色"),
    ("オリジナル", "原创"),
]


def build_content_pack(item: CandidateItem, selection_reason: str) -> dict[str, object]:
    name_cn = human_name(item)
    kind = infer_kind(item.title, item.detail_text)
    motif = infer_motif(item.title, item.detail_text)
    mood = infer_mood(item.title, item.detail_text)
    highlights = item.highlights or ["视觉辨识度很高，适合做轻量种草向内容"]
    tags = build_tags(item, motif, kind)

    summary = (
        f"这次挑中的是「{name_cn}」。"
        f"它更适合写成一条轻松的新品分享，重点放在第一眼的心动感。"
    )

    titles = [
        f"今天被这个{motif}{kind}可爱到了",
        f"Curly 新上的这只{kind}我想先存一下",
        f"如果你喜欢{motif}元素，这只真的会戳你",
        f"这只{kind}属于越看越喜欢那种",
        f"最近很想分享的一个{motif}小东西",
    ]

    hooks = [
        f"今天在 Curly 首页刷到这只 {name_cn}，我第一眼就先停住了。",
        f"如果你最近刚好很吃 {motif} 这种元素，这只 {kind} 应该会让你想点开看细节。",
        f"它不是特别夸张的那种可爱，反而有点安静地戳人。",
    ]

    body = build_post_body(
        item=item,
        name_cn=name_cn,
        kind=kind,
        motif=motif,
        mood=mood,
        highlights=highlights,
    )

    cover = build_cover_copy(item, motif, kind, mood)
    image_plan = build_image_plan(item, cover)
    comments = build_comment_seeds(item, motif, kind)
    checklist = build_review_checklist(item)

    return {
        "summary": summary,
        "selection_reason": selection_reason,
        "post_brief": {
            "goal": "做一条轻量新品情报/心动记录帖，方便人工审核后手动发布",
            "audience": "喜欢日系可爱风、角色杂货、桌搭和挂包小物的女性用户",
            "core_angle": f"分享这只 {motif}{kind} 为什么会让人一眼心动",
            "desired_reader_action": "点开看图、收藏、顺手留言讨论",
        },
        "hooks": hooks,
        "titles": unique_preserve_order(titles)[:5],
        "cover": cover,
        "post_draft": body,
        "tags": tags,
        "comment_seeds": comments,
        "review_checklist": checklist,
        "image_plan": image_plan,
    }


def translate_title(title: str) -> str:
    result = collapse_spaces(title)
    for source, target in TRANSLATIONS:
        result = re.sub(re.escape(source), target, result, flags=re.I)
    result = result.replace(" x ", " x ")
    result = result.replace("ちゃん", "")
    result = result.replace("(", " ").replace(")", " ")
    result = result.replace("☆", " ")
    result = collapse_spaces(result)
    result = result.replace("挂件挂件", "挂件")
    return result


def human_name(item: CandidateItem) -> str:
    raw = translate_title(item.title)
    title_lower = item.title.lower()
    motif = infer_motif(item.title, item.detail_text)
    kind = infer_kind(item.title, item.detail_text)

    if "hello kitty" in title_lower or "ハローキティ" in item.title:
        if motif != "可爱系":
            return f"Hello Kitty {motif}{kind}"
        return f"Hello Kitty {kind}"
    if motif != "可爱系":
        return f"{motif}{kind}"
    return raw


def infer_kind(title: str, detail_text: str) -> str:
    text = f"{title}\n{detail_text}".lower()
    mapping = [
        ("メッシュバッグ", "网眼包"),
        ("バッグ", "包包"),
        ("ポーチ", "收纳包"),
        ("パスケース", "卡套"),
        ("チャーム", "挂件"),
        ("fabric", "布料"),
        ("生地", "布料"),
        ("刺繍", "刺绣小物"),
    ]
    for needle, label in mapping:
        if needle.lower() in text:
            return label
    return "小物"


def infer_motif(title: str, detail_text: str) -> str:
    text = f"{title}\n{detail_text}".lower()
    mapping = [
        ("hello kitty", "Hello Kitty"),
        ("いちご", "草莓"),
        ("チェリー", "樱桃"),
        ("パイナップル", "菠萝"),
        ("リボン", "蝴蝶结"),
        ("ピンク", "粉色"),
        ("ブルー", "蓝色"),
    ]
    for needle, label in mapping:
        if needle in text:
            return label
    return "可爱系"


def infer_mood(title: str, detail_text: str) -> str:
    text = f"{title}\n{detail_text}".lower()
    if "メッシュ" in text or "夏" in text:
        return "清爽春夏"
    if "刺繍" in text:
        return "精致手作"
    if "fabric" in text or "生地" in text:
        return "软乎乎手作"
    return "温柔可爱"


def build_post_body(
    item: CandidateItem,
    name_cn: str,
    kind: str,
    motif: str,
    mood: str,
    highlights: list[str],
) -> dict[str, str]:
    opening = (
        f"今天刷 Curly Collection 的时候，我先被这只「{name_cn}」拽住了视线。"
        f"第一眼不是“哇好夸张”，而是那种会让人想多看两眼的可爱。"
    )

    body_lines = [
        f"这只 {kind} 很适合写成一条轻轻的新品分享，不需要太多铺垫，光看图就已经有记忆点了。",
        f"我自己最先注意到的是它身上的 {motif} 元素，整体是偏 {mood} 的感觉，拿来挂包或者当作最近的小收藏都很顺。",
    ]

    for highlight in highlights[:3]:
        if "价格" in highlight:
            continue
        body_lines.append(f"- {soften_highlight(highlight)}")

    if item.price_text:
        body_lines.append(f"- 页面现在显示的价格是 {item.price_text}，发的时候写“以官网页面为准”会更稳。")

    closing = (
        f"如果你平时也会被这种 {motif} 小细节打到，这只应该会很容易被你顺手存进收藏夹。"
        f"我会把它记成最近看到很想分享的一只。"
    )

    return {
        "opening": opening,
        "body": "\n".join(body_lines),
        "closing": closing,
    }


def build_cover_copy(item: CandidateItem, motif: str, kind: str, mood: str) -> dict[str, str]:
    main_line = f"{motif}{kind}\n有点戳我"
    secondary_line = f"{item.content_type} | {mood}"
    accent = "最近想分享"
    return {
        "main_cover_line": main_line,
        "secondary_cover_line": secondary_line,
        "accent_line": accent,
    }


def build_tags(item: CandidateItem, motif: str, kind: str) -> list[str]:
    tags = [
        "CurlyCollection",
        "日系杂货",
        "可爱小物",
        "新品速递" if item.content_type == "新品速递" else "旧款回看",
        motif,
        kind,
    ]
    return unique_preserve_order(tags)


def build_comment_seeds(item: CandidateItem, motif: str, kind: str) -> list[str]:
    comments = [
        f"这条我先当新品情报记一下，主要是真的被这个 {motif} 细节戳到了。",
        f"如果你也会喜欢这种 {motif} 元素，应该会懂我为什么先把它存下来。",
        "这次不想写得太像种草，更像是把最近看到的可爱小东西分享出来。",
    ]
    if item.price_text:
        comments.append(f"价格我先按页面信息记录成 {item.price_text}，实际还是建议点回官网再确认。")
    return comments[:3]


def build_review_checklist(item: CandidateItem) -> list[str]:
    checklist = [
        "确认标题和正文都没有写成“我已购/我已用”，避免伪装成亲测。",
        "确认价格、材质、容量等信息都来自页面原文，拿不准就删掉。",
        "确认语气像分享，不像客服或促销页。",
        "确认封面文字不要过满，优先保留情绪点和产品类型。",
        "确认图片发布前至少做轻改：弱化背景、重组版式、加中文标题。",
    ]
    checklist.extend(item.uncertainties[:2])
    return checklist


def build_image_plan(item: CandidateItem, cover: dict[str, str]) -> dict[str, object]:
    return {
        "hero_image": item.detail_images[0] if item.detail_images else item.image_url,
        "detail_images": item.detail_images[1:4],
        "layout": "首图用单张大图做轻改背景，正文配图优先 2-4 张细节图，整体做 1 张封面 + 2-3 张补充图。",
        "editing_notes": [
            "背景尽量做柔化或裁切，不直接原样照搬官网构图。",
            "首图加中文大字，副标题保留“新品速递 / 旧款回看”。",
            "如果细节图里出现年份、水印或容易误导的信息，封面里不要放那张。",
        ],
        "cover_copy": cover,
    }


def soften_highlight(text: str) -> str:
    replacements = [
        ("细看容量描述，页面提到 500ml 水瓶也能放进去", "页面写到 500ml 水瓶也能放进去，日常带着出门会更顺手。"),
        ("材质写了 100% 棉，更适合走柔软、好搭配的分享口吻", "页面提到是 100% 棉，整体会更偏柔软、耐看的感觉。"),
        ("有网眼或轻盈材质感，容易写出春夏感和出门搭配感", "这种轻一点的材质很适合写春夏出门的感觉。"),
        ("带挂件或小配饰，细节上更有“可爱完成度”", "带小挂件这一点很加分，可爱感会更完整。"),
        ("有刺绣元素，适合强调手感和小面积点缀的精致感", "如果你平时会留意刺绣细节，这个点会比较好写。"),
        ("本身就是很适合做收纳感内容的小件单品", "这种小件本身就很适合写收纳感和随手带出门。"),
        ("包型单品更容易写出通勤、出门、挂包场景", "包型单品会更容易带出出门、搭配这类场景。"),
        ("页面当前价格显示为", "页面现在显示的价格是"),
    ]
    result = text
    for source, target in replacements:
        result = result.replace(source, target)
    return result
