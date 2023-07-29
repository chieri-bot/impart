
class YinpaConfig:
    max_hp = 1000  # 最大体力
    spend_hp_per_yinpa = 150  # 每次消耗体力
    unit_hp_recovery_seconds = 5  # 回复一点体力所需秒数
    min_persistance = 2.5  # 最低持久要求
    min_hp = -1000  # 最低体力要求

    add_sensitive_every_yinpa = 0.02  # 每次增加的
    add_strength_sensitive_every_yinpa = 2  # 目标力度每次增加的
    red_persistance_overdraft = 1.5  # 透支时扣除的持久力
    red_length_overdraft = 0.1  # 透支时扣除的长度

    sensitive_calc_demarcation = 200  # 敏感度梯队值

    dajiao_add_length = 0.3  # 打胶增加长度
    dajiao_add_chest_size = 0.05
    dajiao_add_sensitive = 1.5  # 打胶增加敏感度
    dajiao_max_magnification = 4  # 打胶最大随机倍率

    snatch_newnew_length_base = 1.0  # 抢夺基本长度
    snatch_newnew_max_magnification = 4  # 抢夺随机数最大倍率
    snatch_opai_length_base = 0.25  # 抢夺基本大小
    snatch_opai_max_magnification = 4  # 抢夺随机数最大倍率

    roll_newnew_base = 2.0  # 随机基本长度
    roll_opai_base = 1.5  # 随机基本长度
    roll_magnification = 3  # 随机倍率范围
