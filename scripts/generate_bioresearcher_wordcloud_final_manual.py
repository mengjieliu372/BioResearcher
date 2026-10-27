from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def build_base_text_image(output: Path) -> tuple[int, int]:
    text = "BioResearcher"
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 260)
    probe = Image.new("RGB", (20, 20), (255, 255, 255))
    pd = ImageDraw.Draw(probe)
    bb = pd.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = 90, 70
    w, h = tw + pad_x * 2, th + pad_y * 2
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((pad_x, pad_y), text, font=font, fill=(0, 0, 0))
    img.save(output)
    return w, h


def build_freq() -> dict[str, int]:
    base = {
        "时间长": 30, "等待": 26, "排队时间长": 24, "速度慢": 23, "代码运行失败": 22, "文献下载失败": 21,
        "报错": 20, "不稳定": 19, "下载失败": 18, "重试": 17, "体验一般": 16, "流程复杂": 15,
        "请求失败": 14, "出错率高": 14, "需要手动干预": 13, "提示不清": 13, "卡住": 12, "好用": 12,
        "中途中断": 12, "工作流等待": 11, "模型调用慢": 11, "占用大": 10, "容易超时": 10, "重复操作": 10,
        "进度不透明": 9, "结果波动": 9, "错误定位难": 9, "上手不快": 8, "资源等待": 8, "后端压力": 8,
        "参数敏感": 7, "网络依赖": 7, "日志难读": 7, "缺少指引": 7, "文档说明不足": 6, "需要清理": 6,
        "偶尔成功": 6, "文件太大": 6, "缺少缓存": 6, "重新运行成本高": 6, "数据质量依赖高": 5, "流程可复现": 5,
        "能跑通": 5, "结果可看": 5, "分析步骤多": 5, "队列阻塞": 5, "任务易堆积": 4, "失败后等待长": 4,
        "接口抖动": 4, "耗时高": 4, "状态反馈少": 4, "下载链路长": 4, "依赖环境多": 4, "并发受限": 4,
        "峰值拥塞": 4, "调试成本高": 4, "容错不足": 4, "可用性一般": 4, "等待资源": 4, "排查慢": 4,
        "日志噪声大": 3, "结果延迟": 3, "回退麻烦": 3, "流程切换慢": 3, "交互反馈弱": 3, "恢复耗时": 3,
        "执行波动": 3, "网络波动影响": 3, "异常重试多": 3, "任务串行": 3, "吞吐偏低": 3, "成功率一般": 3,
        "错误提示少": 3, "步骤依赖强": 3, "操作门槛高": 3, "资源竞争": 3, "代码段失败": 3, "数据准备久": 3,
        "运行窗口长": 3, "等待体验差": 3,
    }
    left = ["流程", "任务", "结果", "日志", "接口", "网络", "模型", "资源", "队列", "并发", "提示", "步骤", "状态", "错误", "参数", "耗时", "吞吐", "缓存", "重试", "恢复", "下载", "上传", "执行", "调试", "排查", "回退", "反馈", "文献", "代码"]
    right = ["偏慢", "不稳", "偏高", "受限", "较弱", "较差", "偏低", "偏长", "易抖动", "不直观", "不友好", "不充分", "不清晰", "不一致", "不可控", "不及时", "不理想", "需优化", "待改进", "有波动"]
    for a in left:
        for b in right:
            key = f"{a}{b}"
            if key not in base:
                base[key] = 1
            if len(base) >= 380:
                return base
    return base


def dedupe_containing_terms(freq: dict[str, int]) -> dict[str, int]:
    ordered = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))
    kept: list[tuple[str, int]] = []
    for word, weight in ordered:
        bad = False
        for w2, _ in kept:
            if word in w2 or w2 in word:
                bad = True
                break
        if not bad:
            kept.append((word, weight))
    return dict(kept)


def main() -> None:
    out = Path("frontend/src/assets/bioresearcher_wordcloud_final.png")
    base_path = Path("frontend/src/assets/bioresearcher_only_preview.png")
    bw, bh = build_base_text_image(base_path)

    width, height = bw + 240, bh + 170
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    base = Image.open(base_path).convert("RGB")
    ox, oy = (width - bw) // 2, (height - bh) // 2
    base_arr = np.array(base)
    text_black_local = (base_arr[:, :, 0] < 20) & (base_arr[:, :, 1] < 20) & (base_arr[:, :, 2] < 20)
    text_black = np.zeros((height, width), dtype=bool)
    text_black[oy:oy + bh, ox:ox + bw] = text_black_local
    # No hard center exclusion: fill whole canvas with words,
    # then render white BioResearcher on top.
    forbid = np.zeros((height, width), dtype=np.uint8)

    freq = dedupe_containing_terms(build_freq())
    items = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    minv, maxv = min(freq.values()), max(freq.values())

    def size_for(v: int) -> int:
        if maxv == minv:
            return 20
        t = (v - minv) / (maxv - minv)
        return int(9 + t * (84 - 9))

    palette = [(24, 104, 224), (35, 116, 230), (44, 126, 235), (56, 137, 239)]
    rng = random.Random(20260403)
    placed: list[tuple[int, int, int, int]] = []

    def hit_forbid(x0: int, y0: int, x1: int, y1: int) -> bool:
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(width - 1, x1)
        y1 = min(height - 1, y1)
        if x1 <= x0 or y1 <= y0:
            return True
        roi = forbid[y0:y1, x0:x1]
        return bool((roi > 0).any())

    def intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int], pad: int = 0) -> bool:
        return not (a[2] + pad < b[0] or a[0] - pad > b[2] or a[3] + pad < b[1] or a[1] - pad > b[3])

    for word, val in items:
        base_size = size_for(val)
        ok = False
        for delta in (0, -2, -4, -6, -8):
            fs = max(8, base_size + delta)
            font = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", fs)
            bb = draw.textbbox((0, 0), word, font=font)
            ww, hh = bb[2] - bb[0], bb[3] - bb[1]
            for _ in range(14000):
                x = rng.randint(1, max(1, width - ww - 1))
                y = rng.randint(1, max(1, height - hh - 1))
                box = (x, y, x + ww, y + hh)
                if hit_forbid(*box):
                    continue
                if any(intersects(box, p, 0) for p in placed):
                    continue
                draw.text((x, y), word, font=font, fill=palette[rng.randrange(len(palette))])
                placed.append(box)
                ok = True
                break
            if ok:
                break

    # Paint center text as pure white final knockout.
    white_layer = np.full((bh, bw, 3), 255, dtype=np.uint8)
    alpha = np.array(
        Image.fromarray(text_black_local.astype(np.uint8) * 255, mode="L").filter(ImageFilter.MaxFilter(size=7))
    )
    img.paste(Image.fromarray(white_layer), (ox, oy), Image.fromarray(alpha, mode="L"))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(out)
    print(f"words={len(freq)} placed={len(placed)} size={width}x{height}")


if __name__ == "__main__":
    main()
