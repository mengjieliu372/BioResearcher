from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from wordcloud import WordCloud


def main() -> None:
    base = Path("frontend/src/assets/bioresearcher_only_preview.png")
    out = Path("frontend/src/assets/bioresearcher_wordcloud_wc_test.png")

    base_img = Image.open(base).convert("RGB")
    bw, bh = base_img.size

    # Keep image only a bit larger than the BioResearcher text.
    width, height = bw + 320, bh + 220
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    ox, oy = (width - bw) // 2, (height - bh) // 2
    canvas.paste(base_img, (ox, oy))
    arr = np.array(canvas)

    # Black text area becomes blocked (white in mask), others are allowed.
    text_black = (arr[:, :, 0] < 30) & (arr[:, :, 1] < 30) & (arr[:, :, 2] < 30)
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[text_black] = 255

    freq = {
        "时间长": 30,
        "等待": 26,
        "排队时间长": 24,
        "速度慢": 23,
        "代码运行失败": 22,
        "文献下载失败": 21,
        "报错": 20,
        "不稳定": 19,
        "下载失败": 18,
        "重试": 17,
        "体验一般": 16,
        "流程复杂": 15,
        "请求失败": 14,
        "出错率高": 14,
        "需要手动干预": 13,
        "提示不清": 13,
        "卡住": 12,
        "好用": 12,
        "中途中断": 12,
        "工作流等待": 11,
        "模型调用慢": 11,
        "占用大": 10,
        "容易超时": 10,
        "重复操作": 10,
        "进度不透明": 9,
        "结果波动": 9,
        "错误定位难": 9,
        "上手不快": 8,
        "资源等待": 8,
        "后端压力": 8,
        "参数敏感": 7,
        "网络依赖": 7,
        "日志难读": 7,
        "缺少指引": 7,
        "文档说明不足": 6,
        "需要清理": 6,
        "偶尔成功": 6,
        "文件太大": 6,
        "缺少缓存": 6,
        "重新运行成本高": 6,
        "数据质量依赖高": 5,
        "流程可复现": 5,
        "能跑通": 5,
        "结果可看": 5,
        "分析步骤多": 5,
        "队列阻塞": 5,
        "任务易堆积": 4,
        "失败后等待长": 4,
        "接口抖动": 4,
        "耗时高": 4,
        "状态反馈少": 4,
        "下载链路长": 4,
        "依赖环境多": 4,
        "并发受限": 4,
        "峰值拥塞": 4,
        "调试成本高": 4,
        "容错不足": 4,
        "可用性一般": 4,
        "等待资源": 4,
        "排查慢": 4,
        "日志噪声大": 3,
        "结果延迟": 3,
        "回退麻烦": 3,
        "流程切换慢": 3,
        "交互反馈弱": 3,
        "恢复耗时": 3,
        "执行波动": 3,
        "网络波动影响": 3,
        "异常重试多": 3,
        "任务串行": 3,
        "吞吐偏低": 3,
        "成功率一般": 3,
        "错误提示少": 3,
        "步骤依赖强": 3,
        "操作门槛高": 3,
        "资源竞争": 3,
        "代码段失败": 3,
        "数据准备久": 3,
        "运行窗口长": 3,
        "等待体验差": 3,
    }

    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        mask=mask,
        font_path=r"C:\Windows\Fonts\simhei.ttf",
        prefer_horizontal=1.0,
        collocations=False,
        random_state=42,
        max_words=500,
        min_font_size=8,
        max_font_size=92,
        margin=1,
        relative_scaling=0.3,
        repeat=False,
        color_func=lambda *args, **kwargs: "#1f6fe5",
    )

    wc.generate_from_frequencies(freq)
    wc.to_file(str(out))
    print(out)


if __name__ == "__main__":
    main()
