import requests

import yinpa
from typing import Optional


def user_info_to_str(user_info: yinpa.m.UserInfo):
    retstr = f"昵称：{user_info.name}\n" \
             f"体力: {user_info.hp} / {yinpa.cfg.max_hp}\n" \
             f"种族: {user_info.body_info.race.value.name}\n" \
             f"-----详细数据-----\n"
    if user_info.sex.isSingle():
        if user_info.length > 0:
            retstr = f"{retstr}基础性别: 男\n○○长度: {user_info.length} cm"
        else:
            retstr = f"{retstr}基础性别: 女\n○○深度: {-user_info.length} cm\n" \
                     f"欧派大小: {user_info.chest_size} ({yinpa.yinpa_tools.chest_size_to_cup(user_info.chest_size)})"
    elif user_info.sex.isDouble():
        retstr = f"{retstr}基础性别: 都有\n○○长度: {user_info.length} cm\n" \
                 f"{retstr}○○深度: {-user_info.length2} cm\n" \
                 f"欧派大小: {user_info.chest_size} ({yinpa.yinpa_tools.chest_size_to_cup(user_info.chest_size)})"
    else:
        retstr = f"{retstr}基础性别: 无"
    retstr = f"{retstr}\n持久度: {user_info.persistance} s\n" \
             f"引乱度: {user_info.prostitution}\n" \
             f"发射: {user_info.shoot_count} 次, {user_info.shoot_vol} 毫升\n" \
             f"被注入: {user_info.injected_count} 次, {user_info.injected_vol} 毫升"
    return retstr

def create_user(userid: int, username: str, sex: int, race: str):
    user_info = yinpa.add_user(userid, username, sex, race)
    return f"创建角色成功:\n{user_info_to_str(user_info)}"

def start_yinpa(self_user_id: int, target_user_id: int, action_name: str, target_part_name: str,
                strength=yinpa.m.StrengthType.NORMAL, group_id=-1):
    data = yinpa.yinpa(self_user_id, target_user_id, action_name, target_part_name, strength, group_id)
    strength_flag = ""
    if strength == yinpa.m.StrengthType.SOFT:
        strength_flag = "轻轻地"
    elif strength == yinpa.m.StrengthType.SEVERELY:
        strength_flag = "狠狠地"
    retstr = f"{data.self_data.name} ({data.self_data.body_info.race.value.name}) {strength_flag}{action_name}了 " \
             f"{data.target_data.name} ({data.target_data.body_info.race.value.name}) 的{target_part_name}\n" \
             f"耗时: {data.use_time} s"
    if data.volume != 0:
        if data.is_serve:
            retstr = f"{retstr}\n{data.target_data.name} 发射了 {data.volume} 毫升"
        else:
            retstr = f"{retstr}\n{data.self_data.name} 向 {data.target_data.name} 注入了 {data.volume} 毫升"
    if data.is_overdraft and (data.reduce_length > 0):
        retstr = f"{retstr}\n{data.self_data.name} 体力透支，导致长度变化: {data.self_data.length} ({-data.reduce_length}) cm"
    retstr = f"{retstr}\n体力变化:\n" \
             f"{data.self_data.name}: {data.self_data.hp} ({-yinpa.cfg.spend_hp_per_yinpa}) / {yinpa.cfg.max_hp}\n" \
             f"{data.target_data.name}: {data.target_data.hp} ({-data.reduce_target_hp}) / {yinpa.cfg.max_hp}\n"
    return retstr

def start_dajiao(user_id: int, body_part_str: Optional[str] = None):
    user_info = yinpa.get_user_info(user_id)
    if body_part_str is not None:
        body_part = yinpa.m.BodyParts.get_pars_from_name(body_part_str)
        if body_part in [yinpa.m.BodyParts.NEWNEW, yinpa.m.BodyParts.NEWNEWHEAD]:
            change_keyword = "长度"
        elif body_part in [yinpa.m.BodyParts.OMANGO, yinpa.m.BodyParts.OMANGOHAPPY]:
            change_keyword = "深度"
        elif body_part in [yinpa.m.BodyParts.CHEST, yinpa.m.BodyParts.NIPPLE]:
            change_keyword = "大小"
        else:
            raise yinpa.err.YinpaValueError(f"{body_part.value.names[0]} 不支持此行为")
    else:
        if user_info.sex.isSingle():
            if user_info.length > 0:
                body_part = yinpa.m.BodyParts.NEWNEW
                change_keyword = "长度"
            else:
                body_part = yinpa.m.BodyParts.OMANGO
                change_keyword = "深度"
        elif user_info.sex.isDouble():  # DOUBLE 如果要扣，必须指定，否则默认打胶
            body_part = yinpa.m.BodyParts.NEWNEW
            change_keyword = "长度"
        elif user_info.sex.isNone():
            body_part = yinpa.m.BodyParts.CHEST
            change_keyword = "大小"
        else:
            raise yinpa.err.YinpaValueError(f"Invalid sex: {user_info.sex}")
    data = yinpa.dajiao(user_id, body_part)
    fanciful_str = ""
    add_str = "增加"
    if not data.user_info.check_have_body_part(data.body_part):
        fanciful_str = "并不存在"
        add_str = "减少"
        if change_keyword == "长度":
            change_keyword = "深度"
        elif change_keyword == "深度":
            change_keyword = "长度"

    current_len = data.user_info.length2 if data.is_len2 else data.user_info.length
    opai_str = ""
    if data.is_opai:
        current_len = data.user_info.chest_size
        opai_str = f" ({yinpa.yinpa_tools.chest_size_to_cup(data.user_info.chest_size)})"
    retstr = f"{data.user_info.name} {data.action.value.names[0]}了自己{fanciful_str}的{data.body_part.value.names[0]}, " \
             f"{change_keyword}{add_str}了 {abs(data.change_value)} cm\n" \
             f"当前状态: {current_len} ({'+' if data.change_value >= 0 else ''}{data.change_value}) cm{opai_str}\n" \
             f"剩余体力: {data.user_info.hp} ({-data.use_hp}) / {yinpa.cfg.max_hp}"
    if (data.user_info.sex.isSingle()) and (data.orig_positive != data.now_positive):  # 变性了
        retstr = f"{retstr}\n\n恭喜 {data.user_info.name} 成功变成了{'女生' if data.user_info.length < 0 else '男生'}\n" \
                 f"(〃'▽'〃)"
    return retstr

def start_snatch(self_user_id: int, target_user_id: int, is_newnew=False, is_opai=False):
    data = yinpa.snatch(self_user_id, target_user_id, is_newnew=is_newnew, is_opai=is_opai)
    target_is_opai = data.body_part == yinpa.m.BodyParts.CHEST
    opai_self_text = ""
    opai_target_text = ""
    if target_is_opai:
        opai_self_text = f" ({yinpa.yinpa_tools.chest_size_to_cup(data.self_data.chest_size)})"
        opai_target_text = f" ({yinpa.yinpa_tools.chest_size_to_cup(data.target_data.chest_size)})"

    retstr = f"{data.self_data.name} 抢夺了 {data.target_data.name} 的{data.body_part.value.names[0]}\n" \
             f"{data.target_data.name} 的{data.body_part.value.names[0]}减少了 {data.snatch_len} cm, " \
             f"剩余 {data.target_data.chest_size if target_is_opai else data.target_data.length} cm{opai_target_text}"
    if data.target_change_sex:
        retstr = f"{retstr}\n{data.target_data.name} 变成了{'男生' if data.target_data.length > 0 else '女生'}"
    if data.self_add:
        retstr = f"{retstr}\n{data.self_data.name} 的{data.body_part.value.names[0]}增加了 {data.snatch_len} cm, " \
                 f"目前 {data.self_data.chest_size if target_is_opai else data.self_data.length} cm{opai_self_text}"
    return retstr

def start_roll_newnew(user_id: int, is_omago=False):
    # is_omago 参数仅用于性别为 DOUBLE 的人指定哪一个
    data = yinpa.newnew_roll(user_id, is_omago=is_omago)
    retstr = f"{data.user_info.name} 进行了一次{data.body_part.value.names[0]}大转盘，获得了 {data.roll_value} cm"
    if data.change_sex:
        retstr = f"{retstr}\n*{data.user_info.name} 变成{'男生' if data.user_info.length > 0 else '女生'}了⁄(⁄⁄•⁄ω⁄•⁄⁄)⁄"
    if data.user_info.sex.isSingle():
        show_len = data.user_info.length
    elif data.user_info.sex.isDouble():
        show_len = data.user_info.length if data.body_part == yinpa.m.BodyParts.NEWNEW else data.user_info.depth
    else:
        raise yinpa.err.YinpaValueError("Invalid sex")
    retstr = f"{retstr}\n当前{'长度' if show_len > 0 else '深度'}: {abs(show_len)}"
    return retstr

def start_roll_opai(user_id: int):
    data = yinpa.opai_roll(user_id)
    return f"{data.user_info.name} 进行了一次{data.body_part.value.names[0]}大转盘，获得了 {data.roll_value} cm\n" \
           f"当前大小: {data.user_info.chest_size} cm ({yinpa.yinpa_tools.chest_size_to_cup(data.user_info.chest_size)})"

def buy_item_coin_callback(userid: int, pay_coin: int):
    # 自行对接你的货币系统
    print(f"{userid} 消耗 {pay_coin} CS点")
    return True

def buy_item(userid: int, item_name: str, count=1):
    user_info, item_info = yinpa.buy_item(userid, item_name, count, buy_item_coin_callback, "CS点数")
    return f"{user_info.name} 购买了 {count} 个{item_name}，当前数量: {user_info.items[item_info]}\n" \
           f"物品描述: {item_info.value.desc}"

def use_item(userid: int, targetid: Optional[int], item_name: str, count=1):
    user_info, target_userinfo, item_info = yinpa.use_item(userid, targetid, item_name, count)
    if item_info.value.target.isSelf():
        retstr = f"{user_info.name} 使用了 {count} 个 {item_name}, 效果: {item_info.value.desc} / 个"
    elif item_info.value.target.isTarget():
        retstr = f"{user_info.name} 对 {target_userinfo.name} 使用了 {count} 个 {item_name}, 效果: {item_info.value.desc} / 个"
    elif item_info.value.target.isBoth():
        retstr = f"{user_info.name} 和 {target_userinfo.name} 使用了 {count} 个 {item_name}, 效果: {item_info.value.desc} / 个"
    else:
        raise yinpa.err.YinpaValueError(f"Invalid item target.")
    return retstr

if __name__ == "__main__":
    # print(user_info_to_str(yinpa.get_user_info(1615)))
    # print(create_user(2248, "sunset", 1, "人类"))
    # print(create_user(1615, "chieri", 1, "猫娘"))

    # print(create_user(2248, "sunset", 1, "人类"))
    # print(create_user(1615, "chieri", 1, "猫娘"))
    #
    # print(start_yinpa(2248, 1615, "透", "小学", yinpa.m.StrengthType.NORMAL, 123456))
    # print(start_dajiao(2248, body_part_str="小学"))
    # print(start_dajiao(1615, body_part_str="欧派"))

    # print(start_snatch(1615, 2248, is_newnew=True))
    # print(start_roll_newnew(2248))
    # print(start_roll_opai(2248))

    # print(buy_item(2248, "变大", 20))
    # print(use_item(2248, 1615, "催情药", 10))
    # print(use_item(2248, 1615, "持久药", 10))

    # yinpa.image_generate.generate_userinfo(yinpa.get_user_info(1615),
    #                                        requests.get("http://q1.qlogo.cn/g?b=qq&nk=1615&s=640").content)

    race_text = ""
    for i, name in enumerate(yinpa.m.RaceTypes):
        race_text += name.value.name
        if (i + 1) % 6 == 0 and i != len(yinpa.m.RaceTypes) - 1:
            race_text += ",\n"
        else:
            race_text += ", "

    rettext = f"""群 yinpa 帮助菜单
管理员指令:
开启本群 yinpa: /yp enable
关闭本群 yinpa: /yp disable

通用指令:
加入yinpa: /yp join 昵称 种族 (种族名请参考下面的种族列表)
离开 yinpa 并删除信息: /yp leave
个人信息 (若要查看他人信息, 请在指令后接@): /yp info
打胶 (增加 敏感度 和 长度/深度): /打个胶先、/打胶、/开导 ...
扣 (效果和打胶相同): /扣、/开扣
抢夺牛牛 (抢夺别人的长度, 若失败, 则倒扣): /抢牛牛 @xxx
大转盘 (随机增减长度/大小): /xx大转盘 (xx请替换成具体部位, 当前支持: 牛牛、芒果、欧派)
银趴:
/(动作)[部位] @xxx 例: /透 @某人、/摸欧派 @某人
/(动作)(对方昵称)[的部位] 例: /透chieri、/摸chieri的欧派

购买道具: /yp buy 物品名 [数量] (物品名请参考下面的物品列表)
使用道具 (若要对他人使用, 请在指令后接@): /yp use 物品名 [数量]

支持的种族:
{race_text}
    """

    yinpa.image_generate.generate_help_img(rettext).save("C:/1234.png")

    pass
