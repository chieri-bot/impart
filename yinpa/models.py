import time
from copy import copy
from pydantic import BaseModel
import typing as t
from enum import Enum
from . import yinpa_error as err


class SignTypes(Enum):
    negative = -1
    zero = 0
    positive = 1


class BaseSex(Enum):
    NONE = 0  # 没有
    SINGLE = 1  # 单极
    DOUBLE = 2  # 都有

    def isNone(self):
        return self.value == BaseSex.NONE.value
    def isSingle(self):
        return self.value == BaseSex.SINGLE.value
    def isDouble(self):
        return self.value == BaseSex.DOUBLE.value

    @staticmethod
    def get_sex_from_value(value: t.Union[int, None]) -> "BaseSex":
        if value is None:
            raise err.YinpaError("Missing required parameter: sex")
        for i in BaseSex:
            if value == i.value:
                return i
        raise err.SexNotFoundError(value)

class CanReadOnlyBaseModel(BaseModel):
    model_read_only: t.Optional[bool] = False

    def __init__(self, read_only=False, **data):
        super().__init__(**data)
        self.model_read_only = read_only

    def __setattr__(self, key, value):
        if self.model_read_only:
            if key != "model_read_only":
                raise AttributeError("Read-only model, attribute assignment not allowed")
        super().__setattr__(key, value)

    def set_read_only(self, value: bool):
        self.model_read_only = value

    def copy_one(self, read_only=False):
        ret = copy(self)
        ret.set_read_only(read_only)
        return ret

class CEnum(Enum):
    def copy_one(self, read_only=False):
        ret = copy(self)
        if hasattr(ret.value, "set_read_only"):
            ret.value.set_read_only(read_only)
        return ret

class StrengthType(Enum):
    SOFT = 0
    NORMAL = 1
    SEVERELY = 2

class DoAction(BaseModel):
    id: int
    names: t.List[str]
    sensitive_addition: float
    is_base_type: bool
    base_strength_type: t.Optional[StrengthType] = StrengthType.NORMAL
    use_self_persistance: t.Optional[bool] = False  # A 对 B 使用动作时，True 以 A 的持久度做计算 (doi)；False 时则以 B 的持久度计算 (侍奉)

class DoActionTypes(Enum):
    STROKE = DoAction(id=0, names=["摸", "摸摸", "抚摸", "抚"], sensitive_addition=0.0, is_base_type=True)
    RUB = DoAction(id=1, names=["撸", "揉", "揉搓"], sensitive_addition=10.0, is_base_type=True)
    PINCH = DoAction(id=2, names=["捏", "捏捏", "揉捏"], sensitive_addition=15.0, is_base_type=True)
    BEAT = DoAction(id=3, names=["拍", "拍打"], sensitive_addition=5.5, is_base_type=True)
    LICK = DoAction(id=4, names=["舔", "舔舐"], sensitive_addition=20.0, is_base_type=True)
    SUCK = DoAction(id=5, names=["吸", "嗦", "吸吮", "吮吸"], sensitive_addition=30.0, is_base_type=True)

    DIG = DoAction(id=6, names=["抠"], sensitive_addition=50.0, is_base_type=False)
    INSERT = DoAction(id=7, names=["透", "插", "草", "操", "日"], sensitive_addition=100.0, use_self_persistance=True, is_base_type=False)

    HIT = DoAction(id=8, names=["打", "击打", "打击"], sensitive_addition=5.5, is_base_type=True, base_strength_type=StrengthType.SEVERELY)
    WHIP = DoAction(id=9, names=["鞭打", "抽打"], sensitive_addition=50.0, is_base_type=True, base_strength_type=StrengthType.SEVERELY)
    CANDLE = DoAction(id=10, names=["滴蜡"], sensitive_addition=45.0, is_base_type=True, base_strength_type=StrengthType.SEVERELY)

    @staticmethod
    def get_action_from_name(name: str):
        for i in DoActionTypes:
            if name in i.value.names:
                return i
        raise err.ActionNotFoundError(name)

class BodyPartsInfo(CanReadOnlyBaseModel):
    body_id: int
    names: t.List[str]
    optional: t.Optional[bool] = False
    need_sex: t.Optional[t.List[BaseSex]] = None
    need_length_sign: t.Optional[t.List[SignTypes]] = None
    base_sensitive: int
    support_actions: t.Optional[t.List[DoActionTypes]] = []
    can_shoot: t.Optional[bool] = False
    can_inject: t.Optional[bool] = False

    def __init__(self, body_id: int, names: t.List[str], base_sensitive=50, optional=False,
                 need_sex: t.Optional[t.List[BaseSex]] = None, need_length_sign: t.Optional[t.List[SignTypes]] = None,
                 support_actions: t.Optional[t.List[DoActionTypes]] = None, read_only=False,
                 can_shoot=False, can_inject=False):
        if support_actions is None:
            support_actions = []
        super().__init__(read_only=read_only, body_id=body_id, names=names, base_sensitive=base_sensitive,
                         optional=optional, need_sex=need_sex, need_length_sign=need_length_sign,
                         support_actions=support_actions, can_shoot=can_shoot, can_inject=can_inject)

    def check_support_action(self, action: DoActionTypes):
        if action.value.is_base_type:
            return True
        return action in self.support_actions

    def get_supported_action_by_name(self, action_name: str):
        action = DoActionTypes.get_action_from_name(action_name)
        if self.check_support_action(action):
            return action
        return None


class BodyParts(CEnum):
    HEAD = BodyPartsInfo(0, ["头"], 50, read_only=True)
    EARS = BodyPartsInfo(1, ["耳朵", "耳"], 190, read_only=True)
    EYES = BodyPartsInfo(2, ["眼睛"], 40, read_only=True)
    FACE = BodyPartsInfo(3, ["脸", "脸颊"], 60, read_only=True)
    NOSE = BodyPartsInfo(4, ["鼻子", "鼻"], 55, read_only=True)
    MOUSE = BodyPartsInfo(5, ["嘴", "嘴巴"], 70, can_inject=True, read_only=True)
    NECK = BodyPartsInfo(6, ["脖子", "脖", "颈"], 180, read_only=True)
    SHOULDER = BodyPartsInfo(7, ["肩膀", "肩", "肩部"], 75, read_only=True)
    ARM = BodyPartsInfo(8, ["手臂", "臂"], 60, read_only=True)
    HANDS = BodyPartsInfo(9, ["手", "手掌"], 40, read_only=True)
    CHEST = BodyPartsInfo(10, ["欧派", "胸", "胸部", "熊", "凶", "奶子", "柰子"], 500, can_shoot=True, read_only=True)  # if man - 300
    NIPPLE = BodyPartsInfo(101, ["奇酷比", "乳头", "奶头", "乃头"], 600, can_shoot=True, read_only=True)  # if man - 300
    ABDOMEN = BodyPartsInfo(11, ["腹部", "腹", "肚子", "肚肚"], 100, read_only=True)
    BACK = BodyPartsInfo(12, ["背", "背部"], 80, read_only=True)
    NEWNEW = BodyPartsInfo(13, ["牛牛", "牛子", "牛至"], 600, need_sex=[BaseSex.SINGLE, BaseSex.DOUBLE],
                           need_length_sign=[SignTypes.positive], can_shoot=True, read_only=True)
    NEWNEWHEAD = BodyPartsInfo(132, ["闺头", "鬼头", "龟头"], 800, need_sex=[BaseSex.SINGLE, BaseSex.DOUBLE],
                               need_length_sign=[SignTypes.positive], can_shoot=True, read_only=True)
    NEWNEWEGG = BodyPartsInfo(133, ["高玩", "蛋蛋", "蛋", "睾丸", "搞完"], 500, need_sex=[BaseSex.SINGLE, BaseSex.DOUBLE],
                              need_length_sign=[SignTypes.positive], read_only=True)
    OMANGO = BodyPartsInfo(131, ["小学", "欧芒果", "小穴"], 600, need_sex=[BaseSex.SINGLE, BaseSex.DOUBLE],
                           need_length_sign=[SignTypes.negative], support_actions=[DoActionTypes.DIG, DoActionTypes.INSERT],
                           can_shoot=True, can_inject=True, read_only=True)
    OMANGOHAPPY = BodyPartsInfo(1311, ["欢乐豆", "小豆豆"], 850, need_sex=[BaseSex.SINGLE, BaseSex.DOUBLE],
                                need_length_sign=[SignTypes.negative], support_actions=[DoActionTypes.DIG],
                                can_shoot=True, can_inject=True, read_only=True)
    ASS = BodyPartsInfo(14, ["屁股", "臀", "臀部", "皮谷"], 500, can_shoot=True, can_inject=True, read_only=True)
    ASSHOLE = BodyPartsInfo(141, ["皮炎", "屁眼", "肛门"], 550, support_actions=[DoActionTypes.DIG, DoActionTypes.INSERT],
                            can_shoot=True, can_inject=True, read_only=True)
    THIGH = BodyPartsInfo(15, ["大腿", "腿"], 100, read_only=True)
    SHANK = BodyPartsInfo(16, ["小腿"], 70, read_only=True)
    FOOT = BodyPartsInfo(17, ["脚", "足"], 100, read_only=True)
    TAIL = BodyPartsInfo(18, ["尾巴", "尾部", "尾"], 200, optional=True, can_shoot=True, read_only=True)
    WING = BodyPartsInfo(19, ["翅膀"], 70, optional=True, read_only=True)
    HALO = BodyPartsInfo(20, ["光环"], 70, optional=True, read_only=True)
    QUIPMENT = BodyPartsInfo(21, ["装备", "舰装"], 70, optional=True, can_inject=True, read_only=True)
    EROMARK = BodyPartsInfo(22, ["淫纹"], 350, optional=True, can_shoot=True, read_only=True)
    HORN = BodyPartsInfo(23, ["角"], 20, optional=True, read_only=True)
    TENEACLE = BodyPartsInfo(24, ["触手"], 300, optional=True, can_shoot=True, read_only=True)

    def __hash__(self):
        return hash(self.value.body_id)

    def __eq__(self, other: "BodyParts"):
        if not isinstance(other, BodyParts):
            return False
        return self.value.body_id == other.value.body_id

    @staticmethod
    def get_parts_from_value(value: t.Union[int, None]) -> "BodyParts":
        if value is None:
            raise err.YinpaError("Missing required parameter: body parts")
        for i in BodyParts:
            if value == i.value.body_id:
                return i
        raise err.BodyNotFoundError(value)

    @staticmethod
    def get_pars_from_name(name: str) -> "BodyParts":
        for i in BodyParts:
            if name in i.value.names:
                return i
        raise err.BodyNotFoundError(name)


class RaceInfo(CanReadOnlyBaseModel):
    race_id: int
    name: str
    has_optional_parts: t.List[BodyParts]
    sensitive_parts: t.List[BodyParts]  # x1.25, 种族特性

    def __init__(self, read_only=False, **data):
        super().__init__(read_only=read_only, **data)


class RaceTypes(Enum):
    HUMAN = RaceInfo(race_id=0, name="人类", has_optional_parts=[], sensitive_parts=[], read_only=True)
    UMAMUSUME = RaceInfo(race_id=1, name="马娘", has_optional_parts=[BodyParts.TAIL],
                         sensitive_parts=[BodyParts.EARS, BodyParts.TAIL, BodyParts.NECK], read_only=True)
    CAT = RaceInfo(race_id=2, name="猫娘", has_optional_parts=[BodyParts.TAIL],
                   sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    DOG = RaceInfo(race_id=3, name="狗娘", has_optional_parts=[BodyParts.TAIL],
                   sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    MOUSE = RaceInfo(race_id=4, name="鼠娘", has_optional_parts=[BodyParts.TAIL],
                   sensitive_parts=[BodyParts.EARS], read_only=True)
    CATTLE = RaceInfo(race_id=5, name="牛娘", has_optional_parts=[BodyParts.TAIL, BodyParts.HORN],
                      sensitive_parts=[BodyParts.ABDOMEN], read_only=True)
    TIGER = RaceInfo(race_id=6, name="虎娘", has_optional_parts=[BodyParts.TAIL],
                     sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    RABBIT = RaceInfo(race_id=7, name="兔娘", has_optional_parts=[BodyParts.TAIL],
                      sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    DRAGON = RaceInfo(race_id=8, name="龙娘", has_optional_parts=[BodyParts.TAIL, BodyParts.WING],
                      sensitive_parts=[BodyParts.EARS, BodyParts.TAIL, BodyParts.WING], read_only=True)
    SNAKE = RaceInfo(race_id=9, name="蛇娘", has_optional_parts=[BodyParts.TAIL], sensitive_parts=[BodyParts.TAIL],
                     read_only=True)
    SHEEP = RaceInfo(race_id=10, name="羊娘", has_optional_parts=[BodyParts.TAIL],
                     sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    MONKEY = RaceInfo(race_id=11, name="猴娘", has_optional_parts=[BodyParts.TAIL],
                      sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    ROOSTER = RaceInfo(race_id=12, name="鸡娘", has_optional_parts=[BodyParts.TAIL, BodyParts.WING],
                       sensitive_parts=[BodyParts.EARS, BodyParts.WING], read_only=True)
    PIG = RaceInfo(race_id=13, name="猪娘", has_optional_parts=[BodyParts.TAIL], sensitive_parts=[], read_only=True)
    ELF = RaceInfo(race_id=14, name="精灵",
                   has_optional_parts=[BodyParts.WING],
                   sensitive_parts=[BodyParts.EARS, BodyParts.WING], read_only=True)
    ANGEL = RaceInfo(race_id=15, name="天使",
                     has_optional_parts=[BodyParts.HALO, BodyParts.WING, BodyParts.NECK],
                     sensitive_parts=[], read_only=True)
    DEMON = RaceInfo(race_id=16, name="魅魔",
                     has_optional_parts=[BodyParts.TAIL, BodyParts.HORN, BodyParts.EROMARK],
                     sensitive_parts=[BodyParts.EROMARK, BodyParts.TAIL, BodyParts.ASS, BodyParts.CHEST,
                                      BodyParts.NIPPLE, BodyParts.NEWNEW, BodyParts.NEWNEWHEAD,
                                      BodyParts.OMANGO, BodyParts.OMANGOHAPPY], read_only=True)
    EVIL = RaceInfo(race_id=17, name="妖精",
                    has_optional_parts=[BodyParts.TAIL, BodyParts.WING],
                    sensitive_parts=[], read_only=True)
    VAMPIRE = RaceInfo(race_id=18, name="吸血鬼",
                       has_optional_parts=[BodyParts.WING, BodyParts.HORN, BodyParts.TAIL],
                       sensitive_parts=[BodyParts.TAIL, BodyParts.MOUSE, BodyParts.NECK], read_only=True)
    MERMAID = RaceInfo(race_id=19, name="人鱼",
                       has_optional_parts=[BodyParts.TAIL],
                       sensitive_parts=[BodyParts.TAIL, BodyParts.CHEST], read_only=True)
    WEREWOLF = RaceInfo(race_id=20, name="狼人",
                        has_optional_parts=[BodyParts.TAIL],
                        sensitive_parts=[BodyParts.TAIL], read_only=True)
    DAPENGU = RaceInfo(race_id=21, name="大喷菇",
                       has_optional_parts=[],
                       sensitive_parts=[BodyParts.HEAD], read_only=True)
    SHIP = RaceInfo(race_id=22, name="舰娘",
                    has_optional_parts=[BodyParts.QUIPMENT],
                    sensitive_parts=[BodyParts.QUIPMENT], read_only=True)
    GUN = RaceInfo(race_id=23, name="枪娘",
                   has_optional_parts=[BodyParts.QUIPMENT],
                   sensitive_parts=[BodyParts.QUIPMENT], read_only=True)
    PENGUIN = RaceInfo(race_id=24, name="企鹅娘", has_optional_parts=[], sensitive_parts=[], read_only=True)
    MECH = RaceInfo(race_id=25, name="机娘",
                    has_optional_parts=[BodyParts.QUIPMENT],
                    sensitive_parts=[BodyParts.QUIPMENT], read_only=True)
    FOX = RaceInfo(race_id=26, name="狐狸",
                   has_optional_parts=[BodyParts.TAIL],
                   sensitive_parts=[BodyParts.EARS, BodyParts.TAIL], read_only=True)
    MONSTER = RaceInfo(race_id=27, name="妖怪",
                       has_optional_parts=[BodyParts.TAIL, BodyParts.WING],
                       sensitive_parts=[], read_only=True)
    TENEACLE = RaceInfo(race_id=28, name="触手娘",
                        has_optional_parts=[BodyParts.TENEACLE],
                        sensitive_parts=[], read_only=True)

    @staticmethod
    def get_race_type_from_id(race_id: t.Optional[t.Union[int, None]]):
        for i in RaceTypes:
            if race_id == i.value.race_id:
                return i
        raise err.RaceNotFoundError(race_id)

    @staticmethod
    def get_race_type_from_name(name: str):
        for i in RaceTypes:
            if name == i.value.name:
                return i
        raise err.RaceNotFoundError(name)


class UserBodyPartsInfo(BaseModel):
    body_id: int
    base_sensitive: int
    sensitive: t.Optional[int] = 0  # 用户更改的
    stroke_soft_sensitive: t.Optional[int] = 0  # 轻轻地摸
    stroke_normal_sensitive: t.Optional[int] = 0  # 摸
    stroke_severely_sensitive: t.Optional[int] = 0  # 狠狠地摸

    def get_sensitive(self):
        return self.sensitive + self.base_sensitive

    @staticmethod
    def init_from_body_parts(data: BodyParts):
        return UserBodyPartsInfo(body_id=data.value.body_id, base_sensitive=data.value.base_sensitive)


class UserBodyInfo(BaseModel):
    race: RaceTypes
    body_parts_info: t.Dict[BodyParts, UserBodyPartsInfo]

    def __init__(self, **data):
        get_race = data.get("race", None)
        if not isinstance(get_race, RaceTypes):
            data["race"] = RaceTypes.get_race_type_from_id(get_race)
        get_body_info = data.get("body_parts_info", {})
        rebuild_body_info = {}
        for k in get_body_info:
            body_parts_base = get_body_info[k]
            if not isinstance(k, BodyParts):
                body_part = BodyParts.get_parts_from_value(int(k))
                body_parts_base["body_id"] = body_part.value.body_id
                body_parts_base["base_sensitive"] = body_part.value.base_sensitive
                rebuild_body_info[body_part] = body_parts_base
            else:
                body_parts_base["body_id"] = k.value.body_id
                body_parts_base["base_sensitive"] = k.value.base_sensitive
                rebuild_body_info[k] = body_parts_base

        data["body_parts_info"] = rebuild_body_info

        super().__init__(**data)
        self.check_body_parts_info()

    def check_body_parts_info(self):
        for i in BodyParts:
            if i in self.body_parts_info:
                self.body_parts_info[i].base_sensitive = i.value.base_sensitive
                continue

            if not i.value.optional:  # 通用部分
                self.body_parts_info[i] = UserBodyPartsInfo.init_from_body_parts(i)
            else:
                if i in self.race.value.has_optional_parts:  # 特有部分
                    self.body_parts_info[i] = UserBodyPartsInfo.init_from_body_parts(i)


class UserInfo(BaseModel):
    id: int
    name: str
    sex: BaseSex
    hp: int
    chest_size: float  # 若为男或无，则忽略此数据
    length: float  # 长度
    length2: t.Optional[float] = 0.0  # 长度2, sex 为 DOUBLE 时有效
    depth: t.Optional[float] = 0.0  # 暂时没用
    prostitution: float  # yl度
    persistance: float  # 持久度
    body_info: UserBodyInfo

    injected_vol: t.Optional[float] = 0.0
    injected_count: t.Optional[int] = 0
    shoot_vol: t.Optional[float] = 0.0
    shoot_count: t.Optional[int] = 0
    last_update_hp: int

    active_time: float  # 主动时间
    passive_time: float  # 被动时间

    def __init__(self, **data):
        get_sex = data.get("sex", None)
        if not isinstance(get_sex, BaseSex):
            data["sex"] = BaseSex.get_sex_from_value(get_sex)

        super().__init__(**data)
        self.update_prostitution()

    @staticmethod
    def check_value(v1, v2, sign: SignTypes):
        if sign == SignTypes.positive:
            return v1 > v2
        elif sign == SignTypes.negative:
            return v1 < v2
        else:
            return v1 == v2

    def check_have_body_part(self, part: BodyParts):
        if part not in self.body_info.body_parts_info:
            return False
        if part.value.need_sex:
            if self.sex not in part.value.need_sex:
                return False
        if part.value.need_length_sign:
            flag = False
            for i in part.value.need_length_sign:
                if self.sex == BaseSex.DOUBLE:
                    if self.check_value(self.length, 0, i) or self.check_value(self.length2, 0, i):
                        flag = True
                        break
                elif self.sex == BaseSex.SINGLE:
                    if self.check_value(self.length, 0, i):
                        flag = True
                        break
                elif self.sex == BaseSex.NONE:
                    return False
                else:
                    raise err.YinpaValueError(f"Invalid sex: {part}")
            if not flag:
                return False
        return True

    def update_prostitution(self):
        value = (self.shoot_vol + self.injected_vol) * (self.injected_count + self.shoot_count) + self.active_time + self.passive_time
        self.prostitution = value
        return value

    def __setattr__(self, key, value):
        if key == "hp":
            self.last_update_hp = int(time.time())
        super().__setattr__(key, value)

    def to_dict(self):
        self.update_prostitution()
        data = self.dict()
        data["sex"] = data["sex"].value
        data["body_info"]["race"] = data["body_info"]["race"].value.race_id
        new_body_parts_info = {}
        for k in data["body_info"]["body_parts_info"]:
            new_body_parts_info[k.value.body_id] = data["body_info"]["body_parts_info"][k]
        data["body_info"]["body_parts_info"] = new_body_parts_info
        return data

    @staticmethod
    def get_init(user_id: int, name: str):
        values = {"id": user_id, "name": name, "sex": BaseSex.SINGLE, "hp": 1000, "chest_size": 1.0,
                  "length": 1, "length2": -1, "depth": 20, "last_update_hp": 0, "active_time": 0, "passive_time": 0,
                  "prostitution": 0, "persistance": 300,
                  "body_info": {
                      "race": RaceTypes.HUMAN,
                      "body_parts_info": {}
                  }}
        return UserInfo(**values)

class ReturnYinpaData(BaseModel):
    self_data: UserInfo
    target_data: UserInfo
    is_overdraft: bool
    volume: float
    reduce_target_hp: int
    reduce_length: float  # 透支扣除长度
    use_time: float
    is_serve: bool

class ReturnDajiaoData(BaseModel):
    user_info: UserInfo
    orig_positive: bool
    now_positive: bool
    change_value: float
    body_part: BodyParts
    action: DoActionTypes
    use_hp: int
    is_len2: bool
    is_opai: bool

    def __init__(self, **data):
        super().__init__(**data)
        assert not (self.is_len2 and self.is_opai), "Invalid boolean: opai and len2"

class ReturnSnatchData(BaseModel):
    self_data: UserInfo
    target_data: UserInfo
    target_change_sex: bool
    self_add: bool
    body_part: BodyParts
    snatch_len: float

class ReturnRollData(BaseModel):
    user_info: UserInfo
    change_sex: bool
    body_part: BodyParts
    roll_value: float

# import json
# values = {"id": 1, "sex": 1, "hp": 100, "chest_size": 10.0, "length": 10, "length2": -10, "depth": 20, "prostitution": 200,
#           "persistance": 250, "body_info": {
#         "race": 0, "body_parts_info": {
#             "0": {},
#             "1": {},
#         }
#     }}
# uinfo = UserInfo(**values)
# print(json.dumps(uinfo.to_dict(), indent=4, ensure_ascii=False))

# print("种族列表")
# for n, i in enumerate(RaceTypes):
#     print(f"[{i.value.race_id}] {i.value.name}")
