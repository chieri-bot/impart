from . import models as m
from PIL import Image, ImageOps, ImageFont, ImageDraw
from io import BytesIO
import os
from typing import List, Any, Union, Tuple, Optional, Callable, Dict
from .config import YinpaConfig as cfg
from . import yinpa_tools


spath = os.path.split(__file__)[0]


def mask_img(img: Image.Image, mask_path: str, size=None) -> Image.Image:
    imsize = img.size if size is None else size
    border = Image.open(mask_path).resize(imsize, Image.ANTIALIAS).convert('L')
    invert = ImageOps.invert(border)
    img.putalpha(invert)
    return img

def draw_table(data: List[List[Any]], table_width=600, table_height=300, bg_color: Union[str, Tuple] = "white",
               font_stze=12, table_title: str = None, draw_colors: Optional[Dict[int, Any]] = None):
    if draw_colors is None:
        draw_colors = {}
    cell_width = table_width / len(data[0])
    cell_height = table_height / (len(data) + (1 if table_title else 0))
    if table_title:
        data = data.copy()
        data.insert(0, [])

    # 创建图像对象
    image = Image.new('RGBA', (table_width, table_height), color=bg_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('msyh.ttc', size=font_stze)

    # 绘制表格线和文本
    for i, row in enumerate(data):
        if (i == 0) and table_title:
            draw.rectangle((0, 0, table_width - 1, cell_height), outline='black')
            title_font = ImageFont.truetype('msyh.ttc', size=font_stze + 1)
            draw.text((table_width / 2, cell_height / 2), str(table_title), fill='black', font=title_font, anchor='mm')
            continue

        fill = draw_colors.get(i + (1 if table_title else 0), "black")
        for j, cell in enumerate(row):
            x = j * cell_width
            y = i * cell_height
            draw.rectangle((x, y, x + cell_width - 1, y + cell_height - 1), outline='black')
            draw.text((x + cell_width / 2, y + cell_height / 2), str(cell), fill=fill, font=font, anchor='mm')
    return image

def paste_image(pt, im, x, y, w=-1, h=-1, with_mask=True):
    w = im.width if w == -1 else w
    h = im.height if h == -1 else h
    im = im.resize((w, h))
    pt.paste(im, (x, y, x + w, y + h), im.convert("RGBA") if with_mask else None)

def img_prop_resize(im: Image.Image, width: int = None, height: int = None):
    w, h = im.size
    if width:
        new_w = width
        new_h = new_w * h / w
    elif height:
        new_h = height
        new_w = new_h * w / h
    else:
        new_w, new_h = w, h
    return im.resize((int(new_w), int(new_h)), Image.ANTIALIAS)

def calc_text_size(text: str, font: ImageFont.FreeTypeFont, line_spacing = 1.0):
    lines = text.split('\n')
    max_line_width = 0
    total_height = 0

    for line in lines:
        line_width, line_height = font.getsize(line)
        max_line_width = max(max_line_width, line_width)
        total_height += line_height * line_spacing
    total_height = int(total_height)
    return max_line_width, total_height


def user_info_to_str(user_info: m.UserInfo):
    retstr = f"昵称: {user_info.name}\n" \
             f"体力: {user_info.hp} / {cfg.max_hp}\n" \
             f"种族: {user_info.body_info.race.value.name}\n"
    if user_info.sex.isSingle():
        if user_info.length > 0:
            retstr = f"{retstr}性别: 男\n\n○○长度:   {user_info.length} cm"
        else:
            retstr = f"{retstr}性别: 女\n\n○○深度:   {-user_info.length} cm\n" \
                     f"欧派大小: {user_info.chest_size} ({yinpa_tools.chest_size_to_cup(user_info.chest_size)})"
    elif user_info.sex.isDouble():
        retstr = f"{retstr}性别: 都有\n\n○○长度:   {user_info.length} cm\n" \
                 f"{retstr}○○深度:   {-user_info.length2} cm\n" \
                 f"欧派大小: {user_info.chest_size} ({yinpa_tools.chest_size_to_cup(user_info.chest_size)})"
    else:
        retstr = f"{retstr}性别: 无\n"
    retstr = f"{retstr}\n持久时间: {user_info.persistance} s\n" \
             f"主动时长: {user_info.active_time} s\n" \
             f"被动时长: {user_info.passive_time} s\n" \
             f"发射次数: {user_info.shoot_count} 次, {user_info.shoot_vol} 毫升\n" \
             f"被注入量: {user_info.injected_count} 次, {user_info.injected_vol} 毫升\n" \
             f"引乱度: {user_info.prostitution}"
    return retstr


def generate_body_info_table(user_info: m.UserInfo, width=490, line_h=25):
    body_info = user_info.body_info
    data = [["部位", "种族基础值", "开发值", "总和"]]
    for k in body_info.body_parts_info:
        if user_info.check_have_body_part(k):
            data.append([k.value.names[0], k.value.base_sensitive, body_info.body_parts_info[k].sensitive,
                         k.value.base_sensitive + body_info.body_parts_info[k].sensitive])
    total_count = len(data)
    return draw_table(data, width, line_h * total_count, (255, 255, 255, 0))


def text_to_img(text: str, text_size=23, margin=15, bg_color: Union[str, Tuple] = "white", line_spacing=1.2):
    font = ImageFont.truetype('msyh.ttc', size=text_size)
    text_w, text_h = calc_text_size(text, font, line_spacing)
    pt = Image.new("RGB", (text_w + margin * 2, text_h + margin * 2), bg_color)
    draw = ImageDraw.Draw(pt)
    draw.text((margin, margin), text, fill="black", font=font)
    return pt


def generate_userinfo(user_info: m.UserInfo, avatar: bytes = None):
    info_str = user_info_to_str(user_info)
    info_str = f"{info_str}\n\n敏感度信息"
    font = ImageFont.truetype('msyh.ttc', size=23)
    text_w, text_h = calc_text_size(info_str, font, 1.2)

    items = [["物品名", "数量/是否装备"]]
    for i in user_info.items:
        _count = user_info.items[i]
        if _count > 0:
            items.append([i.value.names[0], _count])
    for i in user_info.own_dress:
        items.append([i.value.item_names[0], f"1 ({'已装备' if i in user_info.worn_dress else '未装备'})"])

    item_img = img_prop_resize(draw_table(items, 300, 40 * len(items), font_stze=25), width=260)
    body_info_img = generate_body_info_table(user_info)

    body_info_img_y = 20 + text_h + 34
    text_and_body_info_h = body_info_img_y + body_info_img.height
    item_img_h = 267 + item_img.height

    pt = Image.new("RGBA", (max(800, 310 + text_w), max(text_and_body_info_h, item_img_h)), (255, 255, 255, 255))

    try:
        im = Image.open(BytesIO(avatar)) if avatar else Image.open(f"{spath}/res/black_mask.png")  # 头像
        paste_image(pt, mask_img(im.resize((156, 156)), f"{spath}/res/black_mask.png"), 59, 36, 156, 156)
    except BaseException as e:
        print(f"头像图片生成失败: {e}")

    draw = ImageDraw.Draw(pt)
    draw.text((310, 40), info_str, fill="black", font=font)
    font = ImageFont.truetype('msyh.ttc', size=27)
    draw.text((137, 237), "背包物品", fill="black", font=font, anchor='mm')
    paste_image(pt, item_img, 7, 267)
    paste_image(pt, body_info_img, 293, body_info_img_y)
    return pt


def generate_help_img(desc_text: str):
    text_img = text_to_img(desc_text, bg_color=(255, 255, 255, 0), line_spacing=1.2)

    item_data = [["名称", "描述", "使用对象", "价格"]]
    for i in m.ItemTypes:
        if i.value.target.isSelf():
            ts = "自己"
        elif i.value.target.isTarget():
            ts = "对方"
        elif i.value.target.isBoth():
            ts = "双方"
        else:
            ts = "未知"
        item_data.append([", ".join(i.value.names[:4]), i.value.desc, ts, i.value.price])
    for i in m.DressTypes:
        if i.value.can_buy:
            item_data.append([i.value.item_names[0], i.value.description, "自己", i.value.price])

    table_img = draw_table(item_data, 1300, 30 * len(item_data), (255, 255, 255, 0), 12, "物品列表")

    im_w = max(text_img.width, table_img.width) + 15
    im_h = text_img.height + table_img.height
    pt = Image.new("RGBA", (im_w, im_h), "white")
    paste_image(pt, text_img, int((im_w - text_img.width) / 2), 0)
    paste_image(pt, table_img, int((im_w - table_img.width) / 2), text_img.height)
    return pt


def generate_rank_table(head_part: List[m.UserInfo], key: Callable[[m.UserInfo], Any], total_count: int,
                        end_part: Optional[List[m.UserInfo]] = None, title: Optional[str] = None, item_name="数值",
                        target_userinfo: Optional[m.UserInfo] = None, target_user_rank=-1, table_w=350):
    table_data = [["排名", "昵称", item_name]]
    for n, i in enumerate(head_part):
        table_data.append([n + 1, i.name, key(i)])
    target_data_index = -1

    if end_part:
        table_data.append(["...", "...", "..."])
        if target_userinfo:
            if target_userinfo not in head_part:
                if target_userinfo not in end_part:
                    if target_user_rank > 0:
                        target_data_index = len(table_data) + 2
                        table_data.append([target_user_rank, target_userinfo.name, key(target_userinfo)])
                        table_data.append(["...", "...", "..."])
            else:
                target_data_index = head_part.index(target_userinfo) + 3
        end_len = len(end_part)
        for n, i in enumerate(end_part):
            if i.id == target_userinfo.id:
                target_data_index = len(table_data) + 2
            table_data.append([total_count - end_len + n + 1, i.name, key(i)])
    else:
        if target_userinfo:
            if target_userinfo not in head_part:
                table_data.append(["...", "...", "..."])
                if target_user_rank > 0:
                    target_data_index = len(table_data) + 2
                    table_data.append([target_user_rank, target_userinfo.name, key(target_userinfo)])
            else:
                target_data_index = head_part.index(target_userinfo) + 3
    return draw_table(table_data, table_w, 30 * len(table_data), (255, 255, 255, 255), font_stze=13, table_title=title,
                      draw_colors={target_data_index: "red"})


def merge_rank_table_image(ims: List[Image.Image], count_per_line=3, spacing=20):
    rows = len(ims) // count_per_line
    if len(ims) % count_per_line != 0:
        rows += 1

    max_width = max(im.size[0] for im in ims)
    max_height = max(im.size[1] for im in ims)

    table_width = max_width * count_per_line + spacing * (count_per_line - 1)
    table_height = max_height * rows + spacing * (rows - 1)

    table_image = Image.new('RGB', (table_width, table_height), (255, 255, 255))

    for i, im in enumerate(ims):
        row = i // count_per_line
        col = i % count_per_line

        x = col * (max_width + spacing)
        y = row * (max_height + spacing)

        table_image.paste(im, (x, y))

    return table_image
