import random
from . import yinpa_tools
from . import models as m
from . import database
from . import yinpa_error as err
from . import image_generate
from .config import YinpaConfig as cfg
import typing as t
import heapq

db = database.YinpaDB()


def add_user(user_id: int, user_name: str, sex: int, race: str):
    uinfo = db.get_user_info(user_id, raise_notfound_error=False)
    if uinfo is not None:
        raise err.YinpaUserExistsError(f"用户 {user_id} 已存在")

    user_name = user_name.strip()
    if user_name in ["群主", "管理"]:
        raise err.YinpaValueError("不允许使用关键字作为用户名")

    if len(user_name) > 15:
        raise err.YinpaUserError(f"名称过长，请保持在 15 字以内")
    return db.create_user(user_id, user_name, m.BaseSex.get_sex_from_value(sex),
                          m.RaceTypes.get_race_type_from_name(race))


def delete_user(user_id: int):
    return db.delete_user(user_id)


def get_user_info(user_id: int, raise_notfound_error=True):
    return db.get_user_info(user_id, raise_notfound_error=raise_notfound_error)


def get_user_info_by_name(username: str, raise_notfound_error=True):
    return db.get_user_info_from_name(username, raise_notfound_error=raise_notfound_error)


def update_user_info(data: m.UserInfo):
    return db.update_user_info(data)


def yinpa(self_user_id: int, target_user_id: int, action_name: str, target_part_name: str,
          strength=m.StrengthType.NORMAL, group_id=-1):
    """
    开始
    :param self_user_id:发起者id
    :param target_user_id:目标id
    :param action_name:动作名称, 如: 摸, 拍
    :param target_part_name:目标部位
    :param strength:力度
    :param group_id:当前群号
    :return:ReturnYinpaData
    """
    if self_user_id == target_user_id:
        raise err.YinpaUserError("不能对自己做这些事哦，把精力用在群友身上吧~\n(๑•ω•๑)")
    self_user_info = get_user_info(self_user_id, raise_notfound_error=False)
    if self_user_info is None:
        raise err.UserNotFoundError("您还未加入yinpa")
    target_user_info = get_user_info(target_user_id, raise_notfound_error=False)
    if target_user_info is None:
        raise err.UserNotFoundError("对方还未加入yinpa")

    self_hp_left = self_user_info.hp
    is_overdraft = False
    reduce_length = 0
    if self_user_info.hp < cfg.spend_hp_per_yinpa:
        is_overdraft = True
        if self_user_info.hp < cfg.min_hp:
            raise err.YinpaUserError(f"您的体力不足: {self_user_info.hp}\n(；′⌒`)")
    if is_overdraft:  # 透支身体，扣除持久力
        self_user_info.persistance -= cfg.red_persistance_overdraft
        if (self_user_info.length > 0):
            self_user_info.length -= cfg.red_length_overdraft
            reduce_length = cfg.red_length_overdraft

    if self_user_info.persistance < cfg.min_persistance:
        raise err.YinpaUserError(f"你由于过度透支身体, 心有余而力不足, 无法参加。\n"
                                 f"当前持久: {self_user_info.persistance} s\n"
                                 f"至少需要: {cfg.min_persistance} s\n┐(‘～`；)┌")
    self_user_info.hp -= cfg.spend_hp_per_yinpa

    do_action = m.DoActionTypes.get_action_from_name(action_name)
    target_part = m.BodyParts.get_pars_from_name(target_part_name)

    if not target_user_info.check_have_body_part(target_part):
        raise err.YinpaUserError(f"{target_user_info.name} 没有 {target_part_name} 这个部位哦\nヽ(。>д<)ｐ")
    if not target_part.value.check_support_action(do_action):
        raise err.YinpaUserError(f"这个地方不能 {action_name} 哦\n⁄(⁄⁄•⁄ω⁄•⁄⁄)⁄")

    user_target_part_info = target_user_info.body_info.body_parts_info[target_part]
    if strength == m.StrengthType.NORMAL:
        strength = do_action.value.base_strength_type

    total_sensitive = user_target_part_info.get_sensitive()  # 敏感度计算结果
    if strength == m.StrengthType.SOFT:
        total_sensitive += user_target_part_info.stroke_soft_sensitive
        user_target_part_info.stroke_soft_sensitive += cfg.add_strength_sensitive_every_yinpa
    elif strength == m.StrengthType.NORMAL:
        total_sensitive += user_target_part_info.stroke_normal_sensitive
        user_target_part_info.stroke_normal_sensitive += cfg.add_strength_sensitive_every_yinpa
    elif strength == m.StrengthType.SEVERELY:
        total_sensitive += user_target_part_info.stroke_severely_sensitive
        user_target_part_info.stroke_severely_sensitive += cfg.add_strength_sensitive_every_yinpa
    else:
        raise err.YinpaValueError(f"Invalid strength value: {strength}")

    user_target_part_info.sensitive += cfg.add_sensitive_every_yinpa
    if do_action.value.use_self_persistance:  # 耗时计算
        base_time = self_user_info.persistance + self_user_info.temp_use_time
        self_user_info.temp_use_time = 0.0  # 清除临时道具效果
        left_hp_per = self_hp_left / cfg.max_hp
    else:
        base_time = target_user_info.persistance + target_user_info.temp_use_time
        target_user_info.temp_use_time = 0.0  # 清除临时道具效果
        left_hp_per = target_user_info.hp / cfg.max_hp
    use_time = random.randint(int(base_time * left_hp_per * 100), int(base_time * 100)) / 100  # 最终耗时
    volume = yinpa_tools.sensitive_to_volume(total_sensitive + target_user_info.temp_sensitive, use_time)  # 量
    target_user_info.temp_sensitive = 0.0  # 清除临时道具效果
    reduce_target_hp = min(int(volume if volume <= cfg.max_hp / 2 else cfg.max_hp / 2),
                           cfg.spend_hp_per_yinpa)  # 目标减少体力
    target_user_info.hp = int(target_user_info.hp - reduce_target_hp)

    db.update_user_info(self_user_info)
    db.update_user_info(target_user_info)
    db.inject_others(self_user_id, do_action.value.id, target_user_id, target_part.value.body_id, volume, use_time,
                     group_id, not do_action.value.use_self_persistance)

    return m.ReturnYinpaData(self_data=self_user_info, target_data=target_user_info, is_overdraft=is_overdraft,
                             volume=volume, reduce_target_hp=reduce_target_hp, reduce_length=reduce_length,
                             is_serve=not do_action.value.use_self_persistance, use_time=use_time)


def dajiao(userid: int, body_part: m.BodyParts):
    user_info = db.get_user_info(userid)
    if user_info.sex.isNone():  # 无性别不能打
        raise err.YinpaUserError("目标用户没有此功能\n┐(-｡ｰ;)┌")
    need_hp = int(cfg.spend_hp_per_yinpa / 3)  # 需要 1/3 体力
    if user_info.hp < need_hp:
        raise err.YinpaUserError(f"体力不足: {user_info.hp} / {need_hp}")
    user_info.hp -= need_hp
    orig_positive = user_info.length > 0  # 原本是否为正数
    is_len2 = False
    is_opai = False

    add_dajiao = random.randint(cfg.dajiao_add_length * 100,
                                cfg.dajiao_add_length * cfg.dajiao_max_magnification * 100) / 100
    add_chest = random.randint(cfg.dajiao_add_chest_size * 100,
                               cfg.dajiao_add_chest_size * cfg.dajiao_max_magnification * 100) / 100

    if body_part in [m.BodyParts.CHEST, m.BodyParts.NIPPLE]:
        user_info.chest_size += add_chest
        change_value = add_chest
        action = m.DoActionTypes.PINCH
        is_opai = True
    elif body_part in [m.BodyParts.NEWNEW, m.BodyParts.NEWNEWHEAD]:
        user_info.length += add_dajiao
        change_value = add_dajiao
        action = m.DoActionTypes.RUB
    elif body_part in [m.BodyParts.OMANGO, m.BodyParts.OMANGOHAPPY]:
        action = m.DoActionTypes.DIG
        if user_info.sex.isDouble():
            user_info.length2 -= add_dajiao
            change_value = -add_dajiao
            is_len2 = True
        else:
            user_info.length -= add_dajiao
            change_value = -add_dajiao
    else:
        raise err.YinpaValueError(f"body_part {body_part} not support in func: dajiao()")

    add_sensitive = random.randint(int(cfg.dajiao_add_sensitive * 100),
                                   int(cfg.dajiao_add_sensitive * cfg.dajiao_max_magnification * 100)) / 100
    user_info.body_info.body_parts_info[body_part].sensitive += add_sensitive
    now_positive = user_info.length > 0  # 现在是否为正数
    db.update_user_info(user_info)
    return m.ReturnDajiaoData(user_info=user_info, orig_positive=orig_positive, now_positive=now_positive,
                              change_value=change_value, action=action, use_hp=need_hp, is_len2=is_len2,
                              body_part=body_part, is_opai=is_opai, add_sensitive=add_sensitive)


def snatch(self_user_id: int, target_user_id: int, is_newnew=False, is_opai=False):  # 抢夺
    self_user_info = get_user_info(self_user_id)
    target_user_info = get_user_info(target_user_id)
    target_change_sex = False
    self_add = False

    if is_newnew:
        if (target_user_info.length <= 0) or target_user_info.sex.isNone():
            raise err.YinpaUserError(f"用户: {target_user_info.name} 没有这个部位。")
        body_part = m.BodyParts.NEWNEW
        snatch_len = random.randint(int(cfg.snatch_newnew_length_base * 100),
                                    int(cfg.snatch_newnew_length_base * cfg.snatch_newnew_max_magnification * 100)) / 100
        if snatch_len > target_user_info.length:
            if target_user_info.sex.isSingle():
                target_change_sex = True
        target_user_info.length -= snatch_len
        if self_user_info.sex.isSingle():
            if self_user_info.length >= 0:
                self_user_info.length += snatch_len
                self_add = True
        elif self_user_info.sex.isDouble():
            self_user_info.length += snatch_len
            self_add = True
    elif is_opai:
        if (target_user_info.length > 0) and (not target_user_info.sex.isNone()):
            raise err.YinpaUserError(f"用户: {target_user_info.name} 没有这个部位。")
        if target_user_info.chest_size <= 0:
            raise err.YinpaUserError(f"用户: {target_user_info.name} 的欧派没有多余的部分可以抢了。")
        body_part = m.BodyParts.CHEST
        snatch_len = random.randint(int(cfg.snatch_opai_length_base * 100),
                                    int(cfg.snatch_opai_length_base * cfg.snatch_opai_max_magnification * 100)) / 100
        target_user_info.chest_size -= snatch_len
        if target_user_info.chest_size < 0:
            target_user_info.chest_size = 0
        if (self_user_info.length <= 0) or self_user_info.sex.isNone():
            self_user_info.chest_size += snatch_len
            self_add = True
    else:
        raise err.YinpaValueError("snatch() - Invalid parameter.")

    if self_user_info.chest_size < 0:
        self_user_info.chest_size = 0
    if target_user_info.chest_size < 0:
        target_user_info.chest_size = 0

    db.update_user_info(self_user_info)
    db.update_user_info(target_user_info)

    return m.ReturnSnatchData(self_data=self_user_info, target_data=target_user_info, self_add=self_add,
                              target_change_sex=target_change_sex, body_part=body_part, snatch_len=snatch_len)


def newnew_roll(userid: int, is_omago=False):  # 加减大小
    user_info = get_user_info(userid)
    if user_info.sex.isNone():
        raise err.YinpaUserError("目标用户没有这个功能...\n( Ĭ ^ Ĭ )")

    roll_value = random.randint(0, int(cfg.roll_newnew_base * 2 * 100)) / 100 - cfg.roll_newnew_base
    target_change_sex = False
    if user_info.sex.isDouble():
        if is_omago:
            body_part = m.BodyParts.OMANGO
            user_info.length2 += roll_value
            if user_info.length2 > 0:
                user_info.length2 = -0.01
        else:
            body_part = m.BodyParts.NEWNEW
            user_info.length += roll_value
            if user_info.length < 0:
                user_info.length = 0.01
    else:
        orig_is_man = user_info.length > 0
        user_info.length += roll_value
        current_is_man = user_info.length > 0
        if orig_is_man != current_is_man:
            target_change_sex = True
        body_part = m.BodyParts.NEWNEW if orig_is_man else m.BodyParts.OMANGO

    db.update_user_info(user_info)
    return m.ReturnRollData(user_info=user_info, change_sex=target_change_sex, body_part=body_part,
                            roll_value=roll_value)


def opai_roll(userid: int):  # 加减大小
    user_info = get_user_info(userid)
    if user_info.sex.isSingle():
        if user_info.length > 0:
            raise err.YinpaUserError("目标用户欧派目前不可用~\n( Ĭ ^ Ĭ )")

    roll_value = random.randint(0, int(cfg.roll_opai_base * 2 * 100)) / 100 - cfg.roll_opai_base
    user_info.chest_size += roll_value
    if user_info.chest_size < 0:
        user_info.chest_size = 0
    db.update_user_info(user_info)
    return m.ReturnRollData(user_info=user_info, change_sex=False, body_part=m.BodyParts.CHEST, roll_value=roll_value)


def buy_item(userid: int, item_name: str, count=1, coin_use_callback: t.Optional[t.Callable[[int, int], bool]] = None,
             coin_name: str = "CS点数"):
    """
    购买物品
    :param userid: 用户id
    :param item_name: 物品名称
    :param count: 购买数量
    :param coin_use_callback: 货币消耗回调函数。参数1: 用户id，参数2: 需要货币数, 返回值: 消耗成功返回 True，消耗失败返回 False。为 None 则不检查货币
    :param coin_name: 货币名称。当抛出错误时，会使用此名称
    :return:
    """
    user_info = get_user_info(userid)
    item_info = m.ItemTypes.get_item_from_name(item_name)
    if callable(coin_use_callback):
        if not coin_use_callback(userid, item_info.value.price * count):
            raise err.YinpaUserError(f"您的{coin_name}不足, 需要: {item_info.value.price * count}")
    if item_info not in user_info.items:
        user_info.items[item_info] = 0
    user_info.items[item_info] += count
    db.update_user_info(user_info)
    return user_info, item_info


def use_item(self_userid: int, target_userid: t.Optional[int], item_name: str, count=1):
    user_info = get_user_info(self_userid)
    if target_userid is not None:
        target_userinfo = get_user_info(target_userid)
    else:
        target_userinfo = None
    item_info = m.ItemTypes.get_item_from_name(item_name)
    left_count = user_info.items.get(item_info, 0)
    if left_count < count:
        raise err.YinpaUserError(f"物品数量不足，当前数量: {left_count}")

    user_info.items[item_info] -= count

    for i in range(count):
        if item_info.value.target.isSelf():
            user_info.use_item(item_info)
        elif item_info.value.target.isTarget():
            if target_userinfo is None:
                raise err.YinpaUserError(f"此物品只能给别人用哦~")
            target_userinfo.use_item(item_info)
        elif item_info.value.target.isBoth():
            if target_userinfo is not None:
                target_userinfo.use_item(item_info)
            user_info.use_item(item_info)
        else:
            raise err.YinpaValueError("Invalid item target.")

    db.update_user_info(user_info)
    if target_userinfo is not None:
        db.update_user_info(target_userinfo)
    return user_info, target_userinfo, item_info


def get_target_rank(lst, target, key: t.Callable, reverse=False):
    count = 0
    for i in lst:
        if (key(i) > key(target)) if not reverse else (key(i) < key(target)):
            count += 1
    return count + 1


def get_rank_img(userid: int, count_limit=40, limit_users: t.Optional[t.List[int]] = None):
    users_all = db.get_all_users(with_body_parts_info=False)
    users = []
    if limit_users:
        for i in users_all:
            if i.id in limit_users:
                users.append(i)
    else:
        users = users_all

    chest_users = []
    length_users = []
    depth_users = []
    for i in users:
        if i.sex.isSingle():
            if i.length < 0:
                depth_users.append(i)
            else:  # 单 - 男, chest_users 不加
                length_users.append(i)
                continue
        chest_users.append(i)

    target_user = get_user_info(userid, raise_notfound_error=False)

    target_length_rank = 0
    target_depth_rank = 0
    target_chest_rank = 0
    target_prostitution_rank = 0  # yl
    target_persistance_rank = 0  # 耐力
    taregt_injected_vol_rank = 0
    taregt_injected_count_rank = 0
    taregt_shoot_count_rank = 0
    taregt_active_time_rank = 0
    taregt_passive_time_rank = 0
    taregt_shoot_vol_rank = 0

    if target_user:
        if target_user.sex.isSingle():
            if target_user.length < 0:
                target_depth_rank = get_target_rank(depth_users, target_user, lambda u: u.length, reverse=True)
                target_chest_rank = get_target_rank(chest_users, target_user, lambda u: u.chest_size)
            else:
                target_length_rank = get_target_rank(length_users, target_user, lambda u: u.length)
        target_prostitution_rank = get_target_rank(users, target_user, lambda u: u.prostitution)
        target_persistance_rank = get_target_rank(users, target_user, lambda u: u.persistance)
        taregt_injected_vol_rank = get_target_rank(users, target_user, lambda u: u.injected_vol)
        taregt_injected_count_rank = get_target_rank(users, target_user, lambda u: u.injected_count)
        taregt_shoot_count_rank = get_target_rank(users, target_user, lambda u: u.shoot_count)
        taregt_passive_time_rank = get_target_rank(users, target_user, lambda u: u.passive_time)
        taregt_shoot_vol_rank = get_target_rank(users, target_user, lambda u: u.shoot_vol)

    length_rank = heapq.nlargest(int(count_limit / 2), length_users, key=lambda u: u.length)
    length_rank_r = heapq.nsmallest(int(count_limit / 2), length_users, key=lambda u: u.length)
    depth_rank = heapq.nsmallest(int(count_limit / 2), depth_users, key=lambda u: u.length)
    depthrank_r = heapq.nlargest(int(count_limit / 2), depth_users, key=lambda u: u.length)
    persistance_rank = heapq.nlargest(int(count_limit / 2), users, key=lambda u: u.persistance)  # 耐力
    persistance_rank_r = heapq.nsmallest(int(count_limit / 2), users, key=lambda u: u.persistance)  # 耐力, 倒
    prostitution_rank = heapq.nlargest(count_limit, users, key=lambda u: u.prostitution)  # yl
    chest_size_rank = heapq.nlargest(int(count_limit / 2), chest_users, key=lambda u: u.chest_size)
    chest_size_rank_r = heapq.nsmallest(int(count_limit / 2), chest_users, key=lambda u: u.chest_size)

    injected_vol_rank = heapq.nlargest(count_limit, users, key=lambda u: u.injected_vol)
    injected_count_rank = heapq.nlargest(count_limit, users, key=lambda u: u.injected_count)
    shoot_count_rank = heapq.nlargest(count_limit, users, key=lambda u: u.shoot_count)
    shoot_vol_rank = heapq.nlargest(count_limit, users, key=lambda u: u.shoot_vol)
    active_time_rank = heapq.nlargest(count_limit, users, key=lambda u: u.active_time)
    passive_time_rank = heapq.nlargest(count_limit, users, key=lambda u: u.passive_time)

    length_rank_r.reverse()
    depthrank_r.reverse()
    persistance_rank_r.reverse()
    chest_size_rank_r.reverse()

    table_w = 400

    len_tbl = image_generate.generate_rank_table(length_rank, lambda u: u.length, len(length_users),
                                                 end_part=length_rank_r,
                                                 title="长度排行", item_name="长度 (cm)", target_userinfo=target_user,
                                                 target_user_rank=target_length_rank, table_w=table_w)
    depth_tbl = image_generate.generate_rank_table(depth_rank, lambda u: u.length, len(depth_users),
                                                   end_part=depthrank_r,
                                                   title="深度排行", item_name="深度 (cm)", target_userinfo=target_user,
                                                   target_user_rank=target_depth_rank, table_w=table_w)
    persistance_tbl = image_generate.generate_rank_table(persistance_rank, lambda u: u.persistance, len(users),
                                                         end_part=persistance_rank_r, title="持久排行", item_name="持久 (s)",
                                                         target_userinfo=target_user, target_user_rank=target_persistance_rank, table_w=table_w)
    chest_tbl = image_generate.generate_rank_table(chest_size_rank,
                                                   lambda u: f"{u.chest_size} ({yinpa_tools.chest_size_to_cup(u.chest_size)})",
                                                   len(chest_users), end_part=chest_size_rank_r,
                                                   title="欧派排行", item_name="大小", target_userinfo=target_user,
                                                   target_user_rank=target_chest_rank, table_w=table_w)

    injected_vol_tbl = image_generate.generate_rank_table(injected_vol_rank, lambda u: u.injected_vol, len(users),
                                                          end_part=None, title="被注入量排行", item_name="被注入量 (ml)",
                                                          target_userinfo=target_user, target_user_rank=taregt_injected_vol_rank,
                                                          table_w=table_w)
    shoot_vol_tbl = image_generate.generate_rank_table(shoot_vol_rank, lambda u: u.shoot_vol, len(users),
                                                          end_part=None, title="发射量排行", item_name="发射量 (ml)",
                                                          target_userinfo=target_user, target_user_rank=taregt_shoot_vol_rank,
                                                          table_w=table_w)
    injected_count_tbl = image_generate.generate_rank_table(injected_count_rank, lambda u: u.injected_count, len(users),
                                                          end_part=None, title="被透次数排行", item_name="被透次数",
                                                          target_userinfo=target_user, target_user_rank=taregt_injected_count_rank,
                                                          table_w=table_w)
    shoot_count_tbl = image_generate.generate_rank_table(shoot_count_rank, lambda u: u.shoot_count, len(users),
                                                          end_part=None, title="透人次数排行", item_name="透人次数",
                                                          target_userinfo=target_user, target_user_rank=taregt_shoot_count_rank,
                                                          table_w=table_w)
    active_time_tbl = image_generate.generate_rank_table(active_time_rank, lambda u: u.active_time, len(users),
                                                          end_part=None, title="透人总时长排行", item_name="透人时长 (s)",
                                                          target_userinfo=target_user, target_user_rank=taregt_active_time_rank,
                                                          table_w=table_w)
    passive_time_tbl = image_generate.generate_rank_table(passive_time_rank, lambda u: u.passive_time, len(users),
                                                          end_part=None, title="被透总时长排行", item_name="被透时长 (s)",
                                                          target_userinfo=target_user, target_user_rank=taregt_passive_time_rank,
                                                          table_w=table_w)

    prostitution_tbl = image_generate.generate_rank_table(prostitution_rank, lambda u: u.prostitution, len(users),
                                                          end_part=None, title="引乱排行", item_name="引乱度",
                                                          target_userinfo=target_user, target_user_rank=target_prostitution_rank,
                                                          table_w=table_w)

    return image_generate.merge_rank_table_image([len_tbl, depth_tbl, persistance_tbl, chest_tbl, injected_vol_tbl,
                                                  shoot_vol_tbl, injected_count_tbl, shoot_count_tbl, active_time_tbl,
                                                  passive_time_tbl, prostitution_tbl])
