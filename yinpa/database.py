import random
import sqlite3
import os
import time

from . import models
from . import yinpa_error as err
from .config import YinpaConfig as cfg
from . import yinpa_tools

spath = os.path.split(__file__)[0]


class YinpaDB:
    def __init__(self):
        self.conn = sqlite3.connect(f"{spath}/data/yinpa_userinfo.db", check_same_thread=False)

    def update_hp(self, userid):
        cursor = self.conn.cursor()
        query = cursor.execute("SELECT hp, last_update_hp FROM users WHERE id=?", [userid]).fetchone()
        if not query:
            cursor.close()
            raise err.UserNotFoundError(userid)
        db_hp, last_update_hp = query
        time_now = int(time.time())
        now_hp = db_hp + int((time_now - last_update_hp) / cfg.unit_hp_recovery_seconds)
        if now_hp > cfg.max_hp:
            now_hp = cfg.max_hp
        cursor.execute("UPDATE users SET hp=?, last_update_hp=? WHERE id=?", [now_hp, time_now, userid])
        self.conn.commit()
        cursor.close()
        return now_hp

    def get_user_info(self, userid, raise_notfound_error=True):
        self.update_hp(userid)
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row

        query_user = cursor.execute("SELECT * FROM users WHERE id=?", [userid]).fetchone()
        query_body_info = cursor.execute("SELECT * FROM body_info WHERE id=?", [userid]).fetchone()
        query_body_parts_info = cursor.execute("SELECT * FROM body_parts_info WHERE id=?", [userid]).fetchall()
        cursor.close()

        if not all([query_user, query_body_info, query_body_parts_info]):
            if raise_notfound_error:
                raise err.UserNotFoundError(userid)
            else:
                return None

        ret_dict = dict(query_user)
        ret_dict["body_info"] = dict(query_body_info)
        if "body_parts_info" not in ret_dict["body_info"]:
            ret_dict["body_info"]["body_parts_info"] = {}
        for i in query_body_parts_info:
            curr_data = dict(i)
            ret_dict["body_info"]["body_parts_info"][curr_data["body_id"]] = curr_data

        return models.UserInfo(**ret_dict)

    def update_user_info(self, data: models.UserInfo):
        data.update_prostitution()
        cursor = self.conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO users (id, name, sex, hp, chest_size, length, length2, depth, "
                       "prostitution, persistance, injected_vol, injected_count, shoot_vol, shoot_count, active_time, "
                       "passive_time, last_update_hp) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       [data.id, data.name, data.sex.value, data.hp,
                        data.chest_size, data.length, data.length2, data.depth,
                        data.prostitution, data.persistance, data.injected_vol,
                        data.injected_count, data.shoot_vol, data.shoot_count,
                        data.active_time, data.passive_time, data.last_update_hp])
        cursor.execute("INSERT OR REPLACE INTO body_info (id, race) VALUES (?, ?)",
                       [data.id, data.body_info.race.value.race_id])

        for k in data.body_info.body_parts_info:
            v = data.body_info.body_parts_info[k]
            query_parts = cursor.execute("SELECT * FROM body_parts_info WHERE id=? AND body_id=?",
                                         [data.id, k.value.body_id]).fetchone()
            if query_parts:
                cursor.execute("UPDATE body_parts_info SET base_sensitive = ?, sensitive = ?, "
                               "stroke_soft_sensitive = ?, stroke_normal_sensitive = ?, stroke_severely_sensitive = ?"
                               " WHERE id = ? AND body_id = ?", [v.base_sensitive, v.sensitive, v.stroke_soft_sensitive,
                                                                 v.stroke_normal_sensitive, v.stroke_severely_sensitive,
                                                                 data.id, k.value.body_id])
            else:
                cursor.execute("INSERT INTO body_parts_info (id, body_id, base_sensitive, sensitive, "
                               "stroke_soft_sensitive, stroke_normal_sensitive, stroke_severely_sensitive) "
                               "VALUES (?, ?, ?, ?, ?, ?, ?)",
                               [data.id, k.value.body_id, v.base_sensitive, v.sensitive, v.stroke_soft_sensitive,
                                v.stroke_normal_sensitive, v.stroke_severely_sensitive])
        self.conn.commit()
        cursor.close()

    def check_username_exists(self, user_name: str, user_id=None):
        cursor = self.conn.cursor()
        try:
            if user_id is None:
                if cursor.execute("SELECT * FROM users WHERE name=?", [user_name]).fetchone():
                    return True
            else:
                if cursor.execute("SELECT * FROM users WHERE id!=? AND name=?", [user_id, user_name]).fetchone():
                    return True
            return False
        finally:
            cursor.close()

    def create_user(self, user_id: int, user_name: str, sex: models.BaseSex, race: models.RaceTypes):
        if self.check_username_exists(user_name, user_id):
            raise err.YinpaValueError(f"用户名已被使用: {user_name}")

        data = models.UserInfo.get_init(user_id, user_name)
        data.sex = sex
        data.body_info.race = race
        data.length = yinpa_tools.num_limit_absolute(random.randint(0, 400) / 10 - 20, 6.0)
        data.length2 = yinpa_tools.num_limit_absolute(random.randint(0, 400) / 10 - 20, 6.0)
        data.chest_size = random.randint(80, 220) / 10  # None ~ E

        total_len = len(data.body_info.body_parts_info)
        for i in range(10):
            change_value = random.randint(0, 100) - 50
            change_index = random.randint(0, total_len - 1)
            for n, k in enumerate(data.body_info.body_parts_info):
                if n == change_index:
                    data.body_info.body_parts_info[k].sensitive += change_value
                    break

        self.update_user_info(data)
        return data

    def inject_others(self, self_user_id: int, action_type: int, target_user_id: int, target_part: int,
                      volume: float, spend_time: float, group_id=-1, is_serve=False):
        """
        is_serve 为 True 时，仅记录目标用户射出；为 False 时，记录自身射出和目标注入
        """
        cursor = self.conn.cursor()
        try:
            query = cursor.execute("SELECT id FROM users WHERE id=? OR id=?", [self_user_id, target_user_id]).fetchall()
            query = [i[0] for i in query]
            if self_user_id not in query:
                raise err.UserNotFoundError("您还未加入yinpa")
            if target_user_id not in query:
                raise err.UserNotFoundError("对方还未加入yinpa")

            if is_serve:
                cursor.execute("UPDATE users SET shoot_vol = shoot_vol + ?, shoot_count = shoot_count + 1 WHERE id=?",
                               [volume, target_user_id])
            else:
                cursor.execute("UPDATE users SET injected_vol = injected_vol + ?, injected_count = injected_count + 1 "
                               "WHERE id=?", [volume, target_user_id])
                cursor.execute("UPDATE users SET shoot_vol = shoot_vol + ?, shoot_count = shoot_count + 1 WHERE id=?",
                               [volume, self_user_id])

            cursor.execute("UPDATE users SET active_time = active_time + ? WHERE id=?", [spend_time, self_user_id])
            cursor.execute("UPDATE users SET passive_time = passive_time + ? WHERE id=?", [spend_time, target_user_id])
            cursor.execute("INSERT INTO yinpa_log (user_id, action_type, target_id, target_body_part, group_id, inject_volume, timestamp) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?)",
                           [self_user_id, action_type, target_user_id, target_part, group_id, volume, int(time.time())])
            self.conn.commit()
        finally:
            cursor.close()

# yinpadb = YinpaDB()
# uinfo = yinpadb.get_user_info(2248589280)
# print(uinfo)
# yinpadb.create_user(2248589280, "sunset", models.BaseSex.SINGLE, models.RaceTypes.HUMAN)
# yinpadb.create_user(1615694685, "chieri", models.BaseSex.SINGLE, models.RaceTypes.CAT)
# yinpadb.inject_others(2248589280, 1615694685, models.BodyParts.OMANGO.value.body_id, 30.1, 123456)
