import random
from . import yinpa_tools
from . import models as m
from . import database
from . import yinpa_error as err
from .config import YinpaConfig as cfg

db = database.YinpaDB()


def add_user(user_id: int, user_name: str, sex: int, race: str):
    if len(user_name) > 15:
        raise err.YinpaUserError(f"名称过长，请保持在 15 字以内")
    return db.create_user(user_id, user_name, m.BaseSex.get_sex_from_value(sex), m.RaceTypes.get_race_type_from_name(race))

def get_user_info(user_id: int, raise_notfound_error=True):
    return db.get_user_info(user_id, raise_notfound_error=raise_notfound_error)

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
        base_time = self_user_info.persistance
        left_hp_per = self_hp_left / cfg.max_hp
    else:
        base_time = target_user_info.persistance
        left_hp_per = target_user_info.hp / cfg.max_hp
    use_time = random.randint(int(base_time * left_hp_per * 100), int(base_time * 100)) / 100  # 最终耗时
    volume = yinpa_tools.sensitive_to_volume(total_sensitive, use_time)  # 量
    reduce_target_hp = int(volume if volume <= cfg.max_hp / 2 else cfg.max_hp / 2)  # 目标减少体力
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

    if body_part in [m.BodyParts.CHEST, m.BodyParts.NIPPLE]:
        user_info.chest_size += cfg.dajiao_add_chest_size
        change_value = cfg.dajiao_add_chest_size
        action = m.DoActionTypes.PINCH
        is_opai = True
    elif body_part in [m.BodyParts.NEWNEW, m.BodyParts.NEWNEWHEAD]:
        user_info.length += cfg.dajiao_add_length
        change_value = cfg.dajiao_add_length
        action = m.DoActionTypes.RUB
    elif body_part in [m.BodyParts.OMANGO, m.BodyParts.OMANGOHAPPY]:
        action = m.DoActionTypes.DIG
        if user_info.sex.isDouble():
            user_info.length2 -= cfg.dajiao_add_length
            change_value = -cfg.dajiao_add_length
            is_len2 = True
        else:
            user_info.length -= -cfg.dajiao_add_length
            change_value = -cfg.dajiao_add_length
    else:
        raise err.YinpaValueError(f"body_part {body_part} not support in func: dajiao()")

    now_positive = user_info.length > 0  # 现在是否为正数
    db.update_user_info(user_info)
    return m.ReturnDajiaoData(user_info=user_info, orig_positive=orig_positive, now_positive=now_positive,
                              change_value=change_value, action=action, use_hp=need_hp, is_len2=is_len2,
                              body_part=body_part, is_opai=is_opai)

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
