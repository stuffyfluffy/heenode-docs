"""
Монте-Карло модель казны образовательного network state DAO.
Шаг — месяц, горизонт — 60 месяцев. Все суммы в USD (стейблкоины).
"""
import numpy as np
import json, copy

BASE = dict(
    months=60,
    T0=250_000,            # стартовая казна (seed-гранты)
    N0=100,                # активные ученики на старте
    # рост сообщества
    s0=40,                 # базовый приток новых учеников в месяц
    viral=0.10,            # доля N, приводящая новых в месяц (при полной награде)
    reward_pull=0.5,       # насколько приток зависит от уровня наград (0..1)
    churn=0.07,            # отток в месяц
    N_cap=50_000,          # потолок аудитории (логистика)
    # обучение и выплаты
    m=0.15,                # доля учеников с проверенным результатом в месяц
    w_learner=20,          # выплата ученику за результат
    w_teacher=8,           # выплата преподавателю за результат ученика
    w_review=4,            # выплата рецензенту за проверку (не урезается ниже 50%)
    fraud=0.05,            # доля выплат, ушедших sybil-аккаунтам
    # партнёры
    P0=1,                  # партнёров на старте
    P_sales=0.5,           # новых партнёров в месяц от собственных продаж
    P_ref=0.15,            # новых партнёров на один найм (сарафан работодателей)
    P_churn=0.05,          # отток партнёров в месяц
    P_max=200,             # потолок рынка партнёров
    h=0.01,                # доля учеников, готовых к найму в месяц
    place=0.30,            # вероятность трудоустройства готового
    hires_per_partner=0.5, # спрос партнёра, наймов/мес
    fee=2_000,             # комиссия за найм
    bounties_per_partner=1.0, # баунти в месяц на партнёра
    bounty=1_500,          # средний размер баунти (уходит исполнителю)
    take=0.20,             # комиссия казны с баунти
    solver_share=0.05, solver_cap=0.5,   # доля сильных учеников и их пропускная способность
    # гранты и ретро
    grant_p=0.6, grant_med=40_000, grant_sigma=0.6,   # ежеквартальные раунды
    retro_k=3.0, retro_sigma=0.5,                       # раз в 6 мес, $ за результат
    winter_month=None, winter_mult=0.3,                 # «криптозима»
    yield_apy=0.04,
    # расходы
    opex_fixed=10_000, opex_per_user=0.5,
    research_share=0.10,   # доля притоков прошлого квартала на исследования
    # политика казны
    throttle=True, runway_target=12, scale_min=0.2,
    emergency=False, emerg_runway=6, emerg_opex_mult=0.6,   # аварийный режим
    # дополнительные рычаги дохода (по умолчанию выключены)
    sub_per_partner=0,      # подписка партнёра на поиск по графу навыков, $/мес
    seats_per_partner=0, seat_price=0,   # корпоративное обучение сотрудников партнёров
    pledge_rate=0, pledge_amt=0, pledge_months=24,  # добровольные взносы выпускников
    endow=0, endow_apy=0.035, endow_start=12,       # эндаумент по модели Octant: тратится только доходность
    hack_per_year=0, hack_net=0,                     # хакатоны: чистый доход от спонсоров
    extra_opex=0,           # стоимость внедрения рычагов, $/мес
    # платное обучение в поддао
    tuition_share=0, tuition_price=0,   # доля учеников на платном треке и цена, $/мес
    paid_m_mult=1.0, paid_place_mult=1.0, paid_no_rewards=False, scholarship_share=0,
    growth_mult=1.0, churn_mult=1.0,     # влияние цены на приток и отток
    tuition_treasury_share=1.0,          # доля цены когорты, идущая в казну (остальное ментору)
    # лаборатории
    lab_share=0, lab_price=0, lab_take=0.2,          # доля учеников с платным бронированием, цена, комиссия казны
    lab_schol_share=0, lab_schol_cost=0,             # стипендиальные часы: доля учеников, оплата лаборатории казной
    # поэтапный запуск рычагов (месяц, с которого действует)
    fee2=None, fee2_start=0, take2=None, take2_start=0,
    sub_start=0, seats_start=0, pledge_start=0, tuition_start=0, lab_start=0, hack_start=0,
)

def run(p, n_sims=5000, seed=0):
    rng = np.random.default_rng(seed)
    M = p["months"]
    T = np.full(n_sims, float(p["T0"])); N = np.full(n_sims, float(p["N0"]))
    alive = np.ones(n_sims, bool); ruin_month = np.full(n_sims, -1)
    T_hist = np.zeros((M, n_sims)); scale_hist = np.zeros((M, n_sims))
    partner_rev_hist = np.zeros((M, n_sims)); payout_hist = np.zeros((M, n_sims))
    N_hist = np.zeros((M, n_sims))
    E = {k: np.zeros((M, n_sims)) for k in ("learn","teach","rev","research","bounty_net","mentor","lab")}
    own_hist = np.zeros((M, n_sims))
    inflow_q = np.zeros(n_sims); milestones_6 = np.zeros(n_sims)
    burn_avg = np.full(n_sims, p["opex_fixed"] * 1.5)
    partners = np.full(n_sims, float(p["P0"]))
    pledgers = np.zeros(n_sims)
    for t in range(M):
        winter = p["winter_month"] is not None and t >= p["winter_month"]
        grants_on = p.get("grants_until") is None or t < p["grants_until"]
        # политика: масштаб наград по запасу хода
        full_payout = p["m"] * N * (p["w_learner"] + p["w_teacher"] + p["w_review"])
        full_burn = full_payout + p["opex_fixed"] + p["opex_per_user"] * N
        if p["throttle"]:
            scale = np.clip(T / (p["runway_target"] * np.maximum(burn_avg, 1)), p["scale_min"], 1.0)
        else:
            scale = np.ones(n_sims)
        # ученики
        q = p["tuition_share"] if t >= p["tuition_start"] else 0.0
        fee = p["fee2"] if (p["fee2"] is not None and t >= p["fee2_start"]) else p["fee"]
        take = p["take2"] if (p["take2"] is not None and t >= p["take2_start"]) else p["take"]
        sub = p["sub_per_partner"] if t >= p["sub_start"] else 0
        seats = p["seats_per_partner"] * p["seat_price"] if t >= p["seats_start"] else 0
        pledge_rate = p["pledge_rate"] if t >= p["pledge_start"] else 0
        lab_on = t >= p["lab_start"]
        m_eff = p["m"] * ((1 - q) + q * p["paid_m_mult"])
        milestones = m_eff * N
        learner_paid_ms = (1 - q) * p["m"] * N + (0 if p["paid_no_rewards"] else q * p["m"] * p["paid_m_mult"] * N)
        pay_learn = learner_paid_ms * p["w_learner"] * scale
        pay_teach = milestones * p["w_teacher"] * scale
        pay_rev = milestones * p["w_review"] * np.maximum(scale, 0.5)
        payouts = pay_learn + pay_teach + pay_rev
        # мошенничество: часть выплат утекает, результат не создаёт ценности
        real_milestones = milestones * (1 - p["fraud"])
        # партнёры
        ready = p["h"] * N * (1 - p["fraud"]) * ((1 - q) + q * p["paid_place_mult"])
        tuition_gross = q * N * p["tuition_price"] * (1 - p["scholarship_share"])
        tuition = tuition_gross * p["tuition_treasury_share"]
        mentor_pay = tuition_gross - tuition
        lab_paid = p["lab_share"] * N * p["lab_price"] * lab_on
        lab_schol = p["lab_schol_share"] * N * p["lab_schol_cost"] * lab_on
        lab_in = lab_paid * p["lab_take"]
        hires = np.minimum(p["place"] * ready, partners * p["hires_per_partner"])
        bounties_done = np.minimum(partners * p["bounties_per_partner"],
                                   p["solver_share"] * N * (1 - p["fraud"]) * p["solver_cap"])
        partner_rev = (hires * fee + bounties_done * p["bounty"] * take + partners * (sub + seats))
        pledgers = pledgers * (1 - 1 / p["pledge_months"]) + pledge_rate * hires
        extra_in = pledgers * p["pledge_amt"]
        if t >= p["endow_start"]:
            extra_in = extra_in + p["endow"] * p["endow_apy"] / 12 * (0 if winter else 1)
        if p["hack_per_year"] and t >= p["hack_start"] and t % int(12 / p["hack_per_year"]) == int(12 / p["hack_per_year"]) - 1:
            extra_in = extra_in + p["hack_net"] * (0.5 if winter else 1)
        partners = np.minimum(partners * (1 - p["P_churn"]) + p["P_sales"] + p["P_ref"] * hires, p["P_max"])
        # гранты (раз в квартал)
        grants = np.zeros(n_sims)
        if t % 3 == 2:
            hit = rng.random(n_sims) < p["grant_p"]
            size = p["grant_med"] * rng.lognormal(0, p["grant_sigma"], n_sims)
            grants = hit * size * (p["winter_mult"] if winter else 1) * grants_on
        # ретро (раз в полгода, за реальные результаты)
        milestones_6 += real_milestones
        retro = np.zeros(n_sims)
        if t % 6 == 5:
            retro = p["retro_k"] * milestones_6 * rng.lognormal(0, p["retro_sigma"], n_sims)
            retro *= (p["winter_mult"] if winter else 1) * grants_on
            milestones_6[:] = 0
        yld = 0 if winter else np.maximum(T, 0) * p["yield_apy"] / 12
        inflow = partner_rev + grants + retro + yld + extra_in + tuition + lab_in
        own = partner_rev + extra_in + tuition + lab_in - lab_schol   # собственные доходы без грантов, ретро и доходности
        inflow_q += inflow
        emerg = p["emergency"] & (T < p["emerg_runway"] * np.maximum(burn_avg, 1))
        research = 0
        if t % 3 == 2:
            research = p["research_share"] * inflow_q * (~emerg)
            inflow_q[:] = 0
        opex = p["opex_fixed"] * np.where(emerg, p["emerg_opex_mult"], 1.0) + p["opex_per_user"] * N + p["extra_opex"]
        outflow = payouts + opex + research + lab_schol
        T = np.where(alive, T + inflow - outflow, T)
        burn_avg = 0.7 * burn_avg + 0.3 * outflow
        newly_dead = alive & (T <= 0)
        ruin_month[newly_dead] = t; alive &= ~newly_dead
        T = np.where(alive, T, 0)
        N_now = N.copy()
        # динамика аудитории
        attract = (1 - p["reward_pull"]) + p["reward_pull"] * scale
        signups = p["growth_mult"] * (p["s0"] + p["viral"] * N * attract) * (1 - N / p["N_cap"])
        N = np.where(alive, np.maximum(N + signups - p["churn"] * p["churn_mult"] * N, 0), 0)
        E["learn"][t] = np.where(alive | newly_dead, pay_learn, 0); E["teach"][t] = np.where(alive | newly_dead, pay_teach, 0)
        E["rev"][t] = np.where(alive | newly_dead, pay_rev, 0); E["research"][t] = np.where(alive | newly_dead, research, 0)
        E["bounty_net"][t] = np.where(alive | newly_dead, bounties_done * p["bounty"] * (1 - take), 0)
        E["mentor"][t] = np.where(alive | newly_dead, mentor_pay, 0)
        E["lab"][t] = np.where(alive | newly_dead, lab_paid * (1 - p["lab_take"]) + lab_schol, 0)
        own_hist[t] = own
        N_hist[t] = np.where(alive | newly_dead, N_now, 0)
        T_hist[t] = T; scale_hist[t] = scale
        partner_rev_hist[t] = partner_rev; payout_hist[t] = payouts + opex
    return dict(T=T_hist, scale=scale_hist, N=N_hist, prev=partner_rev_hist, E=E, own=own_hist,
                pay=payout_hist, ruin_month=ruin_month, alive=alive)

def summarize(r, M):
    ruin = (r["ruin_month"] >= 0)
    # доля расходов, покрытая собственными доходами (без грантов), скользящее окно 6 мес.
    k = 6; cs_o = np.cumsum(r["own"], axis=0); cs_p = np.cumsum(r["pay"], axis=0)
    roll_o = cs_o.copy(); roll_p = cs_p.copy(); roll_o[k:] -= cs_o[:-k]; roll_p[k:] -= cs_p[:-k]
    selfsuf = roll_o / np.maximum(roll_p, 1)
    med_ss = np.median(selfsuf, axis=1)
    ok = med_ss >= 1
    # первый месяц, начиная с которого покрытие держится >= 1 до конца горизонта
    be = None
    for i in range(len(ok)):
        if ok[i:].all(): be = i; break
    pct = lambda a, q: np.percentile(a, q, axis=1)
    return dict(
        p_ruin_24=float(((r["ruin_month"] >= 0) & (r["ruin_month"] < 24)).mean()),
        p_ruin_60=float(ruin.mean()),
        median_ruin_month=(float(np.median(r["ruin_month"][ruin]) + 1) if ruin.any() else None),
        T_end_p10=float(pct(r["T"], 10)[-1]), T_end_p50=float(pct(r["T"], 50)[-1]),
        T_end_p90=float(pct(r["T"], 90)[-1]),
        min_T_p50=float(np.min(pct(r["T"], 50))),
        min_scale_p50=float(np.min(pct(r["scale"], 50))),
        months_scale_below_half=float(np.mean((r["scale"] < 0.5).sum(axis=0))),
        N_end_p50=float(pct(r["N"], 50)[-1]),
        selfsuf_end_p50=float(med_ss[-1]),
        breakeven_month=(be + 1) if be is not None else None,
        fan=dict(p10=pct(r["T"], 10).round(0).tolist(), p50=pct(r["T"], 50).round(0).tolist(),
                 p90=pct(r["T"], 90).round(0).tolist()),
        selfsuf_med=med_ss.round(3).tolist(),
    )

# v2: рекомендованные рычаги с поэтапным запуском по дорожной карте
V2 = dict(
    fee2=2_700, fee2_start=6,                      # этап 2: комиссия 18% зарплаты
    take2=0.30, take2_start=6,                     # этап 2: комиссия с баунти 30%
    hack_per_year=2, hack_net=25_000, hack_start=5,  # этап 1: хакатоны
    seats_per_partner=4, seat_price=35, seats_start=12,   # этап 2: корпоративные места
    sub_per_partner=250, sub_start=18,             # этап 3: подписка на граф навыков
    pledge_rate=0.3, pledge_amt=40, pledge_start=18,
    tuition_share=0.05, tuition_price=30, scholarship_share=0.2, tuition_treasury_share=0.4,
    paid_m_mult=1.5, paid_place_mult=1.3, paid_no_rewards=True, tuition_start=18,   # этап 3: платные когорты, 60% ментору
    lab_share=0.03, lab_price=40, lab_take=0.2, lab_schol_share=0.01, lab_schol_cost=30, lab_start=24,  # лаборатории
)

SCENARIOS = {
    "base":        ("Базовый", {}),
    "no_throttle": ("Без авторегулятора наград", dict(throttle=False)),
    "winter":      ("Криптозима с 12-го месяца", dict(winter_month=12)),
    "low_place":   ("Слабый найм (10%)", dict(place=0.10)),
    "sybil":       ("Sybil-атака (30% выплат)", dict(fraud=0.30)),
    "no_partners": ("Партнёры не приходят (рынок макс. 10)", dict(P_max=10)),
    "grant_cliff": ("Гранты и ретро кончаются после 24 мес.", dict(grants_until=24)),
    "no_grants":   ("Без грантов и ретро вообще", dict(grants_until=0)),
    "perfect_storm": ("Идеальный шторм: зима + слабый найм + sybil 15%", dict(winter_month=12, place=0.10, fraud=0.15)),
    "storm_no_throttle": ("Шторм без регулятора наград", dict(winter_month=12, place=0.10, fraud=0.15, throttle=False)),
    "storm_emergency": ("Шторм + аварийный режим", dict(winter_month=12, place=0.10, fraud=0.15, emergency=True)),
    "storm_reserve": ("Шторм + стартовая казна $500 тыс.", dict(winter_month=12, place=0.10, fraud=0.15, T0=500_000)),
    "storm_take": ("Шторм + аварийный режим + комиссия баунти 30%", dict(winter_month=12, place=0.10, fraud=0.15, emergency=True, take=0.30)),
}

if __name__ == "__main__":
    out = {}
    for key, (name, ov) in SCENARIOS.items():
        p = copy.deepcopy(BASE); p.update(ov)
        s = summarize(run(p), p["months"]); s["name"] = name
        out[key] = s
        print(f"{name:52s} ruin24={s['p_ruin_24']:.1%} ruin60={s['p_ruin_60']:.1%} "
              f"T_end_p50={s['T_end_p50']:>12,.0f} minscale={s['min_scale_p50']:.2f} "
              f"N_end={s['N_end_p50']:>8,.0f} selfsuf={s['selfsuf_end_p50']:.2f} be={s['breakeven_month']}")
    # чувствительность: каждый параметр ±50% в сценарии «идеальный шторм-lite» (зима)
    sens = {}
    base_p = copy.deepcopy(BASE)
    rs = summarize(run(base_p, 3000), 60); ref = [rs["p_ruin_60"], rs["T_end_p50"]]
    for k in ["w_learner", "m", "fee", "place", "churn", "opex_fixed", "grant_med", "T0", "viral", "P_sales", "take", "fraud"]:
        vals = []
        for f in (0.5, 1.5):
            p = copy.deepcopy(base_p); p[k] = BASE[k] * f
            ss = summarize(run(p, 3000), 60); vals.append([ss["p_ruin_60"], ss["T_end_p50"]])
        sens[k] = dict(low=vals[0], high=vals[1])
    out["_sens"] = dict(ref=ref, data=sens)
    print("sens ref", ref); [print(k, v) for k, v in sens.items()]
    json.dump(out, open("results.json", "w"), ensure_ascii=False)
