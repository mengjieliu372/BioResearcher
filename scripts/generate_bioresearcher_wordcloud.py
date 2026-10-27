from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def pick_font_path() -> str:
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return candidates[-1]


def main() -> None:
    width, height = 2200, 1300
    bg = (244, 246, 250)
    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    font_path = pick_font_path()
    center_text = "BioResearcher"
    center_font = ImageFont.truetype(font_path, 210)

    # Prepare knockout mask for center text.
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    text_box = mask_draw.textbbox((0, 0), center_text, font=center_font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    text_x = (width - text_w) // 2
    text_y = (height - text_h) // 2
    mask_draw.text((text_x, text_y), center_text, fill=255, font=center_font)

    forbidden = mask.copy()
    forbidden_draw = ImageDraw.Draw(forbidden)
    forbidden_draw.rectangle(
        (text_x - 20, text_y - 20, text_x + text_w + 20, text_y + text_h + 20),
        fill=255,
    )

    # Each term appears exactly once. Size reflects counts.
    terms: list[tuple[str, int]] = [
        ("时间长", 30),
        ("等待", 26),
        ("排队时间长", 24),
        ("速度慢", 23),
        ("代码运行失败", 22),
        ("文献下载失败", 21),
        ("报错", 20),
        ("不稳定", 19),
        ("下载失败", 18),
        ("重试", 17),
        ("体验一般", 16),
        ("流程复杂", 15),
        ("请求失败", 14),
        ("出错率高", 14),
        ("需要手动干预", 13),
        ("提示不清", 13),
        ("卡住", 12),
        ("中途中断", 12),
        ("好用", 12),
        ("工作流等待", 11),
        ("模型调用慢", 11),
        ("占用大", 10),
        ("容易超时", 10),
        ("重复操作", 10),
        ("进度不透明", 9),
        ("结果波动", 9),
        ("错误定位难", 9),
        ("上手不快", 8),
        ("资源等待", 8),
        ("后端压力", 8),
        ("参数敏感", 7),
        ("网络依赖", 7),
        ("日志难读", 7),
        ("缺少指引", 7),
        ("文档说明不足", 6),
        ("需要清理", 6),
        ("偶尔成功", 6),
        ("文件太大", 6),
        ("缺少缓存", 6),
        ("重新运行成本高", 6),
        ("数据质量依赖高", 5),
        ("流程可复现", 5),
        ("能跑通", 5),
        ("结果可看", 5),
        ("分析步骤多", 5),
        ("队列阻塞", 5),
        ("任务易堆积", 4),
        ("失败后等待长", 4),
        ("接口抖动", 4),
        ("耗时高", 4),
        ("状态反馈少", 4),
        ("下载链路长", 4),
        ("依赖环境多", 4),
        ("并发受限", 4),
        ("峰值拥塞", 4),
        ("调试成本高", 4),
        ("容错不足", 4),
        ("可用性一般", 4),
        ("等待资源", 4),
        ("排查慢", 4),
        ("日志噪声大", 3),
        ("结果延迟", 3),
        ("回退麻烦", 3),
        ("流程切换慢", 3),
        ("交互反馈弱", 3),
        ("恢复耗时", 3),
        ("执行波动", 3),
        ("网络波动影响", 3),
        ("异常重试多", 3),
        ("任务串行", 3),
        ("吞吐偏低", 3),
        ("成功率一般", 3),
        ("错误提示少", 3),
        ("步骤依赖强", 3),
        ("操作门槛高", 3),
        ("资源竞争", 3),
        ("代码段失败", 3),
        ("数据准备久", 3),
        ("运行窗口长", 3),
        ("等待体验差", 3),
        ("界面反馈慢", 3),
        ("处理链路长", 3),
        ("偶发超时", 3),
        ("文献获取慢", 3),
        ("任务恢复慢", 3),
        ("信息提示弱", 3),
        ("输入校验弱", 3),
        ("运行波动大", 3),
        ("耗时不可控", 3),
        ("上传等待长", 3),
        ("下载重试多", 3),
        ("报错不直观", 3),
        ("失败提示笼统", 3),
        ("失败排查慢", 3),
        ("进度条不准", 3),
        ("结果预览慢", 3),
        ("流程回退慢", 3),
        ("任务编排复杂", 3),
        ("重跑成本高", 3),
        ("日志定位慢", 3),
        ("步骤衔接紧", 3),
        ("参数影响大", 3),
        ("网络要求高", 3),
        ("吞吐不足", 3),
        ("性能波动", 3),
        ("等待占比高", 3),
        ("执行时间久", 3),
        ("处理效率低", 3),
        ("任务积压", 3),
        ("峰值时延高", 3),
        ("故障恢复慢", 3),
        ("容错路径少", 3),
        ("调用链偏长", 3),
        ("依赖过多", 3),
        ("接口稳定性弱", 3),
        ("数据读取慢", 3),
        ("调参成本高", 3),
        ("结果一致性弱", 3),
        ("重试次数多", 3),
        ("故障提示少", 3),
        ("信息过载", 3),
        ("任务阻塞", 3),
        ("资源占压", 3),
        ("后台排队", 3),
        ("链接易断", 3),
        ("流程等待", 3),
        ("中间步骤慢", 3),
        ("排队反馈弱", 3),
        ("处理吞吐低", 3),
        ("请求抖动", 3),
        ("步骤繁琐", 3),
        ("调试不便", 3),
        ("模型等待长", 3),
        ("结果返回慢", 3),
        ("整体偏慢", 3),
    ]

    # Add many unique low-frequency fillers to improve density (each appears once).
    filler_left = [
        "流程", "任务", "结果", "日志", "接口", "网络", "模型", "资源", "队列", "并发",
        "提示", "步骤", "状态", "错误", "参数", "耗时", "吞吐", "缓存", "重试", "恢复",
        "等待", "下载", "上传", "执行", "调试", "排查", "回退", "反馈", "文献", "代码",
    ]
    filler_right = [
        "偏慢", "不稳", "偏高", "受限", "较弱", "较差", "偏低", "偏长", "易抖动", "不直观",
        "不友好", "不充分", "不清晰", "不一致", "不可控", "不及时", "不理想", "需优化", "待改进", "有波动",
    ]
    existing = {k for k, _ in terms}
    for a in filler_left:
        for b in filler_right:
            phrase = f"{a}{b}"
            if phrase in existing:
                continue
            terms.append((phrase, 1))
            existing.add(phrase)
            if len(terms) >= 320:
                break
        if len(terms) >= 320:
            break

    terms.sort(key=lambda x: x[1], reverse=True)
    min_freq = min(v for _, v in terms)
    max_freq = max(v for _, v in terms)
    palette = [(16, 86, 187), (27, 102, 206), (39, 117, 218), (52, 131, 228), (68, 147, 236)]

    def size_for(freq: int) -> int:
        t = 0 if max_freq == min_freq else (freq - min_freq) / (max_freq - min_freq)
        return int(10 + t * (86 - 10))

    def intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int], pad: int = 2) -> bool:
        return not (a[2] + pad < b[0] or a[0] - pad > b[2] or a[3] + pad < b[1] or a[1] - pad > b[3])

    def in_forbidden(box: tuple[int, int, int, int]) -> bool:
        x0, y0, x1, y1 = box
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(width - 1, x1)
        y1 = min(height - 1, y1)
        step = 5
        for yy in range(y0, y1, step):
            for xx in range(x0, x1, step):
                if forbidden.getpixel((xx, yy)) > 0:
                    return True
        return False

    occupied: list[tuple[int, int, int, int]] = []
    rnd = random.Random(20260403)
    cx, cy = width // 2, height // 2
    placed_count = 0

    for word, freq in terms:
        base_size = size_for(freq)
        placed = False

        for delta in (0, -4, -8, -12):
            fsize = max(16, base_size + delta)
            font = ImageFont.truetype(font_path, fsize)
            wb = draw.textbbox((0, 0), word, font=font)
            ww = wb[2] - wb[0]
            hh = wb[3] - wb[1]

            # Uniform full-canvas fill to keep density high and distributed.
            for _ in range(18000):
                px = rnd.randint(6, max(6, width - ww - 6))
                py = rnd.randint(6, max(6, height - hh - 6))
                box = (px, py, px + ww, py + hh)
                if in_forbidden(box):
                    continue
                if any(intersects(box, b, 0) for b in occupied):
                    continue
                draw.text((px, py), word, font=font, fill=palette[rnd.randrange(len(palette))])
                occupied.append(box)
                placed = True
                placed_count += 1
                break
            if placed:
                break

    # White center text only, without any outline or glow.
    draw.text((text_x, text_y), center_text, fill=(255, 255, 255), font=center_font)

    out = Path("frontend/src/assets/bioresearcher_wordcloud_v4.png")
    image.save(out)
    print(f"saved={out} total_terms={len(terms)} placed={placed_count}")


if __name__ == "__main__":
    main()
