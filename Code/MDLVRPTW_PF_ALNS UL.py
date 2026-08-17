import math
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

def _make_unique_point(candidate: Tuple[float, float], used: Set[Tuple], forbidden: Set[Tuple], step: float=5.0) -> Tuple[float, float]:
    x, y = candidate
    shifts = [(0, 0), (step, 0), (-step, 0), (0, step), (0, -step), (step, step), (step, -step), (-step, step), (-step, -step), (2 * step, 0), (-2 * step, 0), (0, 2 * step), (0, -2 * step)]
    for dx, dy in shifts:
        p = (x + dx, y + dy)
        if p not in forbidden and p not in used:
            return p
    k = 3
    while True:
        p = (x + k * step, y + k * step)
        if p not in forbidden and p not in used:
            return p
        k += 1

def _depot_extra_points(n_extra: int, x_min: float, y_min: float, x_max: float, y_max: float) -> List[Tuple[float, float]]:
    if n_extra <= 0:
        return []
    corners_cycle = [(x_min, y_min), (x_max, y_min), (x_min, y_max), (x_max, y_max)]
    if n_extra == 2:
        return [(x_min, y_min), (x_max, y_max)]
    if n_extra <= 4:
        return corners_cycle[:n_extra]
    mid_x, mid_y = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
    pts = corners_cycle + [(mid_x, y_min), (mid_x, y_max), (x_min, mid_y), (x_max, mid_y), (mid_x, mid_y)]
    ring = 2
    while len(pts) < n_extra:
        frac = 1.0 / (ring + 1)
        pts.append((x_min + frac * (x_max - x_min), y_min + frac * (y_max - y_min)))
        pts.append((x_max - frac * (x_max - x_min), y_max - frac * (y_max - y_min)))
        ring += 1
    return pts[:n_extra]

@dataclass
class Instance:
    name: str
    I: List[int]
    V: List[int]
    J: List[int]
    N: List[int]
    coords: Dict[int, Tuple[float, float]]
    D: Dict[int, float]
    p_unit: Dict[int, float]
    s: Dict[int, float]
    a: Dict[int, float]
    b: Dict[int, float]
    pi: Dict[int, float]
    delta: Dict[int, float]
    t: Dict[Tuple[int, int], float]
    c: Dict[Tuple[int, int], float]
    C_depot: Dict[int, float]
    K_depot: Dict[int, int]
    Q: Dict[int, float]

    def dist(self, i: int, j: int) -> float:
        xi, yi = self.coords[i]
        xj, yj = self.coords[j]
        return math.hypot(xi - xj, yi - yj)

def read_solomon_file(file_path: str, n_customers: int) -> Tuple[Tuple[float, float], Dict[int, Dict]]:
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.split()
            if len(tokens) < 7:
                continue
            try:
                values = [float(x) for x in tokens[:7]]
            except ValueError:
                continue
            rows.append(values)
    if not rows:
        raise ValueError(f'No Solomon customer rows found in {file_path!r}.')
    depot_row = next((row for row in rows if int(row[0]) == 0), None)
    if depot_row is None:
        raise ValueError('Solomon depot row (customer 0) was not found.')
    customer_rows = [row for row in rows if int(row[0]) > 0]
    if n_customers > len(customer_rows):
        raise ValueError(f'Requested {n_customers} customers, but file contains only {len(customer_rows)}.')
    raw = {}
    for row in customer_rows[:n_customers]:
        cid, x, y, demand, ready, due, service = row
        raw[int(cid)] = {'x': x, 'y': y, 'd': demand, 'a': ready, 'b': due, 's': service}
    return ((depot_row[1], depot_row[2]), raw)

def build_instance_from_file(file_path: str, dataset: str, n_customers: int=20, n_depots: int=3) -> Instance:
    if n_customers < 1:
        raise ValueError('n_customers must be >= 1')
    if n_depots < 1:
        raise ValueError('n_depots must be >= 1')
    depot_origin, raw_customers = read_solomon_file(file_path, n_customers)
    orig_ids = list(raw_customers.keys())
    I = list(range(n_depots))
    J = list(range(n_depots, n_depots + n_customers))
    V = list(range(25))
    N = I + J
    customers = {new_id: dict(raw_customers[orig_id]) for new_id, orig_id in zip(J, orig_ids)}
    x_vals = [customers[j]['x'] for j in J]
    y_vals = [customers[j]['y'] for j in J]
    x_min, x_max = (min(x_vals), max(x_vals))
    y_min, y_max = (min(y_vals), max(y_vals))
    cust_pts = {(customers[j]['x'], customers[j]['y']) for j in J}
    raw_depots = [depot_origin] + _depot_extra_points(n_depots - 1, x_min, y_min, x_max, y_max)
    used = set()
    depot_coords = {}
    for i, candidate in enumerate(raw_depots):
        if i == 0:
            depot_coords[i] = depot_origin
        else:
            depot_coords[i] = _make_unique_point(candidate, used, cust_pts, step=5.0)
        used.add(depot_coords[i])
    coords = {i: depot_coords[i] for i in I}
    coords.update({j: (customers[j]['x'], customers[j]['y']) for j in J})
    D = {j: float(customers[j]['d']) for j in J}
    p_unit = {j: 8.0 for j in J}
    s = {n: 0.0 for n in N}
    s.update({j: float(customers[j]['s']) for j in J})
    a = {j: float(customers[j]['a']) for j in J}
    b = {j: float(customers[j]['b']) for j in J}
    pi = {j: 100.0 if D[j] <= 20 else 150.0 for j in J}
    delta = {j: 3.0 for j in J}
    C_depot = {i: 20.0 for i in I}
    K_depot = {i: 5 for i in I}
    Q = {v: 200.0 for v in V}

    def dist(i: int, j: int) -> float:
        xi, yi = coords[i]
        xj, yj = coords[j]
        return math.hypot(xi - xj, yi - yj)
    t = {(i, j): dist(i, j) for i in N for j in N if i != j}
    c = dict(t)
    return Instance(name=f'{dataset}_{n_customers}c_{n_depots}d', I=I, V=V, J=J, N=N, coords=coords, D=D, p_unit=p_unit, s=s, a=a, b=b, pi=pi, delta=delta, t=t, c=c, C_depot=C_depot, K_depot=K_depot, Q=Q)

@dataclass
class Config:
    iters: int = 5000
    segment: int = 100
    q_min: int = 2
    q_max_ratio: float = 0.4
    patience: int = 500
    min_improvement: float = 1e-09
    w_start_pct: float = 0.05
    cooling: float = 0.99975
    sigma1: float = 33.0
    sigma2: float = 9.0
    sigma3: float = 13.0
    reaction: float = 0.1
    phi_noise: float = 0.025
    allow_new_routes: bool = True
    seed: int = 7
    destroy_ops: Optional[List[str]] = None
    repair_ops: Optional[List[str]] = None
    tau_init: float = 1.5
    tau_min: float = 0.35
    eps_explore: float = 0.05
    beta_R: float = 1.2
    beta_A: float = 0.8
    beta_I: float = 1.5
    beta_G: float = 0.3
    beta_V: float = 1.0
    beta_C: float = 1.0
    beta_P: float = 1.0
    age_scale: float = 100.0
    beta_prob: float = 1.0
    beta_modified: float = 1.0
    lambda_hybrid: float = 0.5

@dataclass
class RouteEval:
    distance: float = 0.0
    lateness_cost: float = 0.0
    profit: float = 0.0
    shortage_cost: float = 0.0
    arrival: Dict[int, float] = field(default_factory=dict)
    late: Dict[int, float] = field(default_factory=dict)
    delivered: Dict[int, float] = field(default_factory=dict)
    remaining_cap: float = 0.0

@dataclass
class Solution:
    routes: Dict[int, List[int]]
    depot_of: Dict[int, Optional[int]]
    unserved: Set[int]
    obj: float = 0.0
    evals: Dict[int, RouteEval] = field(default_factory=dict)
    opened: Set[int] = field(default_factory=set)

    def copy(self) -> 'Solution':
        return Solution(routes={v: list(r) for v, r in self.routes.items()}, depot_of=dict(self.depot_of), unserved=set(self.unserved), obj=self.obj, evals={}, opened=set(self.opened))

@dataclass
class Result:
    method: str
    instance_name: str
    seed: int
    best_solution: Solution
    history: Dict[str, Any]
    runtime_sec: float
    objective: float = 0.0
    profit: float = 0.0
    routing_cost: float = 0.0
    facility_cost: float = 0.0
    shortage_penalty: float = 0.0
    lateness_penalty: float = 0.0
    opened_depots: List[int] = field(default_factory=list)
    n_used_vehicles: int = 0
    n_served_customers: int = 0

def _make_empty(inst: Instance) -> Solution:
    return Solution(routes={v: [] for v in inst.V}, depot_of={v: None for v in inst.V}, unserved=set(inst.J))

def _start_route(sol: Solution, v: int, depot: int) -> None:
    sol.depot_of[v] = depot
    sol.routes[v] = [depot, depot]

def _eval_route(route: List[int], v: int, inst: Instance) -> RouteEval:
    re = RouteEval()
    if not route or len(route) < 2:
        re.remaining_cap = inst.Q[v]
        return re
    cap = inst.Q[v]
    time_now = 0.0
    dist_sum = 0.0
    customers_in_order: List[int] = []
    for idx in range(len(route) - 1):
        i, j = (route[idx], route[idx + 1])
        if i != j:
            dist_sum += inst.c[i, j]
        if j in inst.J:
            time_now += inst.t[i, j]
            start_svc = max(time_now, inst.a[j])
            late = max(0.0, start_svc - inst.b[j])
            re.arrival[j] = start_svc
            re.late[j] = late
            re.lateness_cost += inst.delta[j] * late
            customers_in_order.append(j)
            time_now = start_svc + inst.s[j]
        else:
            time_now += inst.t[i, j] if i != j else 0.0
    re.distance = dist_sum
    unique_c = list(dict.fromkeys(customers_in_order))
    vals = {j: inst.p_unit[j] + inst.pi[j] for j in unique_c}
    q_alloc = {j: 0.0 for j in unique_c}
    remaining = cap
    for j in sorted(unique_c, key=lambda j: vals[j], reverse=True):
        if remaining <= 1e-09:
            break
        take = min(inst.D[j], remaining)
        q_alloc[j] = take
        remaining -= take
    re.remaining_cap = remaining
    for j in unique_c:
        qj = q_alloc[j]
        re.delivered[j] = qj
        re.profit += inst.p_unit[j] * qj
        re.shortage_cost += inst.pi[j] * (inst.D[j] - qj)
    return re

def eval_solution(sol: Solution, inst: Instance) -> Solution:
    opened: Set[int] = set()
    depot_vc: Dict[int, int] = {d: 0 for d in inst.I}
    total_profit = total_dist = total_late = total_short = 0.0
    evals: Dict[int, RouteEval] = {}
    served: Set[int] = set()
    for v in inst.V:
        r = sol.routes.get(v, [])
        if not r:
            continue
        d = sol.depot_of.get(v)
        if d is None:
            continue
        opened.add(d)
        depot_vc[d] += 1
        re = _eval_route(r, v, inst)
        evals[v] = re
        total_profit += re.profit
        total_dist += re.distance
        total_late += re.lateness_cost
        total_short += re.shortage_cost
        served |= {j for j, qj in re.delivered.items() if qj > 1e-09}
    for j in inst.J:
        if j not in served:
            total_short += inst.pi[j] * inst.D[j]
    fac = sum((inst.C_depot[d] for d in opened))
    sol.evals = evals
    sol.opened = opened
    for d in inst.I:
        if depot_vc[d] > inst.K_depot[d]:
            sol.obj = total_profit - total_dist - fac - total_short - total_late - 1000000.0
            return sol
    sol.obj = total_profit - total_dist - fac - total_short - total_late
    return sol

def _prune(sol: Solution, inst: Instance) -> Solution:
    sol = sol.copy()
    eval_solution(sol, inst)
    for v in inst.V:
        r = sol.routes.get(v, [])
        if not r or len(r) <= 2:
            continue
        re = sol.evals.get(v)
        if re is None:
            continue
        depot = r[0]
        new_route = [depot]
        for node in r[1:-1]:
            if node in inst.J:
                if re.delivered.get(node, 0.0) > 1e-09:
                    new_route.append(node)
                else:
                    sol.unserved.add(node)
            else:
                new_route.append(node)
        new_route.append(depot)
        if len(new_route) <= 2:
            sol.routes[v] = []
            sol.depot_of[v] = None
        else:
            sol.routes[v] = new_route
    eval_solution(sol, inst)
    return sol

def _customers_in(sol: Solution, inst: Instance) -> Set[int]:
    return {n for v in inst.V for n in sol.routes.get(v, []) if n in inst.J}

def _used_vehicles(sol: Solution) -> int:
    return sum((1 for r in sol.routes.values() if r))

def _routing_cost(sol: Solution) -> float:
    return sum((re.distance for re in sol.evals.values()))

def _sol_hash(sol: Solution, inst: Instance) -> tuple:
    return tuple(((v, sol.depot_of.get(v), tuple(sol.routes.get(v, []))) for v in inst.V))

def _best_insert(route: List[int], v: int, cust: int, inst: Instance, noise_max: float=0.0) -> Tuple[float, Optional[int]]:
    base = _make_empty(inst)
    base.routes[v] = list(route)
    base.depot_of[v] = route[0]
    base.unserved = set(inst.J) - {n for n in route if n in inst.J}
    eval_solution(base, inst)
    base_obj = base.obj
    best_delta, best_pos = (-1e+18, None)
    for pos in range(1, len(route)):
        nr = route[:pos] + [cust] + route[pos:]
        tmp = _make_empty(inst)
        tmp.routes[v] = nr
        tmp.depot_of[v] = nr[0]
        tmp.unserved = set(inst.J) - {n for n in nr if n in inst.J}
        eval_solution(tmp, inst)
        tmp = _prune(tmp, inst)
        eval_solution(tmp, inst)
        stays = any((n == cust for n in tmp.routes[v])) if tmp.routes.get(v) else False
        dobj = tmp.obj - base_obj if stays else -1e+18
        if noise_max > 0.0 and dobj > -1e+17:
            dobj += random.uniform(-noise_max, noise_max)
        if dobj > best_delta:
            best_delta, best_pos = (dobj, pos)
    return (best_delta, best_pos)

def _repair_greedy(sol: Solution, inst: Instance, noise_on: bool, noise_max: float, allow_new: bool) -> Solution:
    sol = sol.copy()
    eval_solution(sol, inst)
    sol = _prune(sol, inst)
    U = set(sol.unserved)
    while U:
        best = None
        for cust in U:
            for v in inst.V:
                if not sol.routes[v]:
                    if not allow_new:
                        continue
                    for d in inst.I:
                        tmp = sol.copy()
                        _start_route(tmp, v, d)
                        eval_solution(tmp, inst)
                        if sum((1 for vv in inst.V if tmp.depot_of.get(vv) == d and tmp.routes.get(vv))) > inst.K_depot[d]:
                            continue
                        di, pos = _best_insert(tmp.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                        if pos is not None and (best is None or di > best[0]):
                            best = (di, cust, v, pos, d, True)
                else:
                    di, pos = _best_insert(sol.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                    if pos is not None and (best is None or di > best[0]):
                        best = (di, cust, v, pos, sol.depot_of[v], False)
        if best is None or best[0] <= 1e-09:
            break
        _, cust, v, pos, d, is_new = best
        if is_new:
            _start_route(sol, v, d)
        sol.routes[v] = sol.routes[v][:pos] + [cust] + sol.routes[v][pos:]
        sol.unserved.discard(cust)
        eval_solution(sol, inst)
        sol = _prune(sol, inst)
        U = set(sol.unserved)
    return sol

def _repair_regret(sol: Solution, inst: Instance, k: int, noise_on: bool, noise_max: float, allow_new: bool) -> Solution:
    sol = sol.copy()
    eval_solution(sol, inst)
    sol = _prune(sol, inst)
    U = set(sol.unserved)
    while U:
        best_choice = None
        for cust in U:
            options = []
            for v in inst.V:
                if not sol.routes[v]:
                    if not allow_new:
                        continue
                    for d in inst.I:
                        tmp = sol.copy()
                        _start_route(tmp, v, d)
                        eval_solution(tmp, inst)
                        if sum((1 for vv in inst.V if tmp.depot_of.get(vv) == d and tmp.routes.get(vv))) > inst.K_depot[d]:
                            continue
                        di, pos = _best_insert(tmp.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                        if pos is not None:
                            options.append((di, v, pos, d, True))
                else:
                    di, pos = _best_insert(sol.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                    if pos is not None:
                        options.append((di, v, pos, sol.depot_of[v], False))
            if not options:
                continue
            options.sort(key=lambda x: x[0], reverse=True)
            best_opt = options[0]
            topk = options[:max(1, min(k, len(options)))]
            regret = sum((best_opt[0] - o[0] for o in topk[1:]))
            cand = (regret, best_opt[0], cust, best_opt[1], best_opt[2], best_opt[3], best_opt[4])
            if best_choice is None or cand[0] > best_choice[0] or (cand[0] == best_choice[0] and cand[1] > best_choice[1]):
                best_choice = cand
        if best_choice is None or best_choice[1] <= 1e-09:
            break
        _, _, cust, v, pos, d, is_new = best_choice
        if is_new:
            _start_route(sol, v, d)
        sol.routes[v] = sol.routes[v][:pos] + [cust] + sol.routes[v][pos:]
        sol.unserved.discard(cust)
        eval_solution(sol, inst)
        sol = _prune(sol, inst)
        U = set(sol.unserved)
    return sol

def _repair_blink(sol: Solution, inst: Instance, blink_prob: float=0.15, allow_new: bool=True) -> Solution:
    sol = sol.copy()
    eval_solution(sol, inst)
    sol = _prune(sol, inst)
    U = set(sol.unserved)
    while U:
        cands = []
        for cust in U:
            for v in inst.V:
                if not sol.routes[v]:
                    if not allow_new:
                        continue
                    for d in inst.I:
                        tmp = sol.copy()
                        _start_route(tmp, v, d)
                        eval_solution(tmp, inst)
                        if sum((1 for vv in inst.V if tmp.depot_of.get(vv) == d and tmp.routes.get(vv))) > inst.K_depot[d]:
                            continue
                        di, pos = _best_insert(tmp.routes[v], v, cust, inst)
                        if pos is not None:
                            cands.append((di, cust, v, pos, d, True))
                else:
                    di, pos = _best_insert(sol.routes[v], v, cust, inst)
                    if pos is not None:
                        cands.append((di, cust, v, pos, sol.depot_of[v], False))
        if not cands:
            break
        cands.sort(key=lambda x: x[0], reverse=True)
        idx = 0
        while idx < len(cands) - 1 and random.random() < blink_prob:
            idx += 1
        di, cust, v, pos, d, is_new = cands[idx]
        if di <= 1e-09:
            break
        if is_new:
            _start_route(sol, v, d)
        sol.routes[v] = sol.routes[v][:pos] + [cust] + sol.routes[v][pos:]
        sol.unserved.discard(cust)
        eval_solution(sol, inst)
        sol = _prune(sol, inst)
        U = set(sol.unserved)
    return sol

def _remove_nodes(sol: Solution, inst: Instance, customers: List[int]) -> Solution:
    sol = sol.copy()
    to_rm = set(customers)
    for v in inst.V:
        r = sol.routes.get(v, [])
        if not r:
            continue
        d = r[0]
        nr = [d] + [n for n in r[1:-1] if not (n in inst.J and n in to_rm)] + [d]
        if len(nr) <= 2:
            sol.routes[v] = []
            sol.depot_of[v] = None
        else:
            sol.routes[v] = nr
    for c in customers:
        sol.unserved.add(c)
    eval_solution(sol, inst)
    sol = _prune(sol, inst)
    return sol

def _remove_random(sol: Solution, inst: Instance, q: int) -> Tuple[Solution, List[int]]:
    served = list(_customers_in(sol, inst))
    if not served:
        return (sol.copy(), [])
    rem = random.sample(served, k=min(q, len(served)))
    return (_remove_nodes(sol, inst, rem), rem)

def _relatedness(i: int, j: int, Ti: float, Tj: float, inst: Instance, w_d: float=9.0, w_t: float=3.0, w_l: float=2.0) -> float:
    max_d = max((inst.dist(a, b) for a in inst.N for b in inst.N if a != b))
    max_t = max(inst.b.values()) + 1e-09
    max_l = max(inst.D.values()) + 1e-09
    return w_d * inst.dist(i, j) / max_d + w_t * abs(Ti - Tj) / max_t + w_l * abs(inst.D[i] - inst.D[j]) / max_l

def _remove_shaw(sol: Solution, inst: Instance, q: int, p: float=6.0) -> Tuple[Solution, List[int]]:
    sol = sol.copy()
    eval_solution(sol, inst)
    served = list(_customers_in(sol, inst))
    if not served:
        return (sol, [])
    r0 = random.choice(served)
    removed = [r0]
    Tcust = {j: tj for v in inst.V for j, tj in (sol.evals[v].arrival.items() if sol.evals.get(v) else [])}
    while len(removed) < min(q, len(served)):
        r = random.choice(removed)
        cands = [x for x in served if x not in removed]
        if not cands:
            break
        cands.sort(key=lambda x: _relatedness(r, x, Tcust.get(r, 0.0), Tcust.get(x, 0.0), inst))
        idx = min(int(random.random() ** p * len(cands)), len(cands) - 1)
        removed.append(cands[idx])
    return (_remove_nodes(sol, inst, removed), removed)

def _remove_string(sol: Solution, inst: Instance, q: int, max_len: int=3) -> Tuple[Solution, List[int]]:
    sol = sol.copy()
    cr = [(v, [n for n in sol.routes.get(v, []) if n in inst.J]) for v in inst.V]
    cr = [(v, cs) for v, cs in cr if cs]
    if not cr:
        return (sol, [])
    removed: List[int] = []
    while len(removed) < q and cr:
        v, _ = random.choice(cr)
        custs = [n for n in sol.routes.get(v, []) if n in inst.J]
        if not custs:
            cr = [(vv, [n for n in sol.routes.get(vv, []) if n in inst.J]) for vv in inst.V]
            cr = [(vv, cs) for vv, cs in cr if cs]
            continue
        L = min(max_len, len(custs), q - len(removed))
        if L <= 0:
            break
        sl = random.randint(1, L)
        si = random.randint(0, len(custs) - sl)
        string = custs[si:si + sl]
        removed.extend(string)
        sol = _remove_nodes(sol, inst, string)
        cr = [(vv, [n for n in sol.routes.get(vv, []) if n in inst.J]) for vv in inst.V]
        cr = [(vv, cs) for vv, cs in cr if cs]
    return (sol, list(dict.fromkeys(removed)))

def _remove_worst(sol: Solution, inst: Instance, q: int, p: float=3.0) -> Tuple[Solution, List[int]]:
    sol = sol.copy()
    eval_solution(sol, inst)
    served = list(_customers_in(sol, inst))
    if not served:
        return (sol, [])
    L = sorted([(sol.obj - (lambda tmp: (eval_solution(tmp, inst), tmp.obj)[1])(_remove_nodes(sol.copy(), inst, [c])), c) for c in served], key=lambda x: x[0])
    removed: List[int] = []
    for _ in range(min(q, len(L))):
        idx = min(int(random.random() ** p * len(L)), len(L) - 1)
        removed.append(L[idx][1])
        L.pop(idx)
    return (_remove_nodes(sol, inst, removed), removed)

def _remove_vehicle_min(sol: Solution, inst: Instance, q: int) -> Tuple[Solution, List[int]]:
    sol = sol.copy()
    active = {v: [n for n in sol.routes.get(v, []) if n in inst.J] for v in inst.V if sol.routes.get(v)}
    active = {v: cs for v, cs in active.items() if cs}
    if not active:
        return (sol, [])
    target_v = min(active, key=lambda v: len(active[v]))
    removed = active[target_v][:q] if len(active[target_v]) > q else active[target_v]
    return (_remove_nodes(sol, inst, removed), removed)

def _remove_profit_max(sol: Solution, inst: Instance, q: int) -> Tuple[Solution, List[int]]:
    sol = sol.copy()
    eval_solution(sol, inst)
    profit_contrib: Dict[int, float] = {}
    for v in inst.V:
        re = sol.evals.get(v)
        if re:
            for j, q_del in re.delivered.items():
                profit_contrib[j] = inst.p_unit[j] * q_del
    served = list(_customers_in(sol, inst))
    if not served:
        return (sol, [])
    served.sort(key=lambda c: profit_contrib.get(c, 0.0))
    removed = served[:min(q, len(served))]
    return (_remove_nodes(sol, inst, removed), removed)

def _remove_cost_min(sol: Solution, inst: Instance, q: int) -> Tuple[Solution, List[int]]:
    sol = sol.copy()
    eval_solution(sol, inst)
    served = list(_customers_in(sol, inst))
    if not served:
        return (sol, [])
    savings: List[Tuple[float, int]] = []
    for c in served:
        for v in inst.V:
            r = sol.routes.get(v, [])
            if c not in r:
                continue
            idx = r.index(c)
            pred, succ = (r[idx - 1], r[idx + 1])
            saving = inst.dist(pred, c) + inst.dist(c, succ) - inst.dist(pred, succ)
            savings.append((saving, c))
            break
    savings.sort(reverse=True)
    removed = [c for _, c in savings[:min(q, len(savings))]]
    return (_remove_nodes(sol, inst, removed), removed)

def _repair_random(sol: Solution, inst: Instance, allow_new: bool) -> Solution:
    sol = sol.copy()
    eval_solution(sol, inst)
    sol = _prune(sol, inst)
    U = set(sol.unserved)
    while U:
        cust = random.choice(list(U))
        inserted = False
        vehicles = list(inst.V)
        random.shuffle(vehicles)
        for v in vehicles:
            if sol.routes.get(v):
                r = sol.routes[v]
                pos = random.randint(1, len(r) - 1)
                nr = r[:pos] + [cust] + r[pos:]
                tmp = sol.copy()
                tmp.routes[v] = nr
                tmp.unserved.discard(cust)
                eval_solution(tmp, inst)
                tmp = _prune(tmp, inst)
                eval_solution(tmp, inst)
                if any((n == cust for n in tmp.routes.get(v, []))):
                    sol = tmp
                    inserted = True
                    break
            elif allow_new:
                for d in inst.I:
                    tmp = sol.copy()
                    _start_route(tmp, v, d)
                    if sum((1 for vv in inst.V if tmp.depot_of.get(vv) == d and tmp.routes.get(vv))) > inst.K_depot[d]:
                        continue
                    pos = 1
                    tmp.routes[v] = [d, cust, d]
                    tmp.unserved.discard(cust)
                    eval_solution(tmp, inst)
                    tmp = _prune(tmp, inst)
                    eval_solution(tmp, inst)
                    if any((n == cust for n in tmp.routes.get(v, []))):
                        sol = tmp
                        inserted = True
                        break
                if inserted:
                    break
        U = set(sol.unserved)
    return sol

def _repair_deep_greedy(sol: Solution, inst: Instance, noise_on: bool, noise_max: float, allow_new: bool) -> Solution:
    sol = sol.copy()
    eval_solution(sol, inst)
    sol = _prune(sol, inst)
    U = list(sol.unserved)
    if not U:
        return sol
    scores: List[Tuple[float, int]] = []
    for cust in U:
        best_delta = -1e+18
        for v in inst.V:
            if sol.routes.get(v):
                di, _ = _best_insert(sol.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                if di > best_delta:
                    best_delta = di
        scores.append((best_delta, cust))
    scores.sort(key=lambda x: x[0])
    for _, cust in scores:
        if cust not in sol.unserved:
            continue
        best = None
        for v in inst.V:
            if not sol.routes[v]:
                if not allow_new:
                    continue
                for d in inst.I:
                    tmp = sol.copy()
                    _start_route(tmp, v, d)
                    eval_solution(tmp, inst)
                    if sum((1 for vv in inst.V if tmp.depot_of.get(vv) == d and tmp.routes.get(vv))) > inst.K_depot[d]:
                        continue
                    di, pos = _best_insert(tmp.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                    if pos is not None and (best is None or di > best[0]):
                        best = (di, v, pos, d, True)
            else:
                di, pos = _best_insert(sol.routes[v], v, cust, inst, noise_max if noise_on else 0.0)
                if pos is not None and (best is None or di > best[0]):
                    best = (di, v, pos, sol.depot_of[v], False)
        if best is None or best[0] <= 1e-09:
            continue
        _, v, pos, d, is_new = best
        if is_new:
            _start_route(sol, v, d)
        sol.routes[v] = sol.routes[v][:pos] + [cust] + sol.routes[v][pos:]
        sol.unserved.discard(cust)
        eval_solution(sol, inst)
        sol = _prune(sol, inst)
    return sol

def _init_state(names: List[str]) -> Dict[str, Dict]:
    return {k: {'weight': 1.0, 'score': 0.0, 'use': 0, 'recent_reward': 0.0, 'accept_rate': 0.5, 'improve_rate': 0.1, 'age': 10.0, 'vehicle_saving': 0.0, 'routing_saving': 0.0, 'profit_saving': 0.0} for k in names}

def _reset_scores(state: Dict[str, Dict]) -> None:
    for k in state:
        state[k]['score'] = 0.0
        state[k]['use'] = 0

def _update_state(state: Dict[str, Dict], chosen: str, reward: float, accepted: bool, improved: bool, vsave: float, rsave: float, psave: float=0.0, sigma1: float=33.0, rsmooth: float=0.8, asmooth: float=0.85, ismooth: float=0.9, ssmooth: float=0.85) -> None:
    for k in state:
        state[k]['age'] += 1.0
    rn = max(0.0, reward) / max(1e-09, sigma1)
    st = state[chosen]
    st['score'] += reward
    st['use'] += 1
    st['recent_reward'] = rsmooth * st['recent_reward'] + (1 - rsmooth) * rn
    st['accept_rate'] = asmooth * st['accept_rate'] + (1 - asmooth) * (1.0 if accepted else 0.0)
    st['improve_rate'] = ismooth * st['improve_rate'] + (1 - ismooth) * (1.0 if improved else 0.0)
    st['vehicle_saving'] = ssmooth * st['vehicle_saving'] + (1 - ssmooth) * vsave
    st['routing_saving'] = ssmooth * st['routing_saving'] + (1 - ssmooth) * rsave
    st['profit_saving'] = ssmooth * st['profit_saving'] + (1 - ssmooth) * psave
    if reward > 0 or improved:
        st['age'] = 0.0

def _update_weights(state: Dict[str, Dict], reaction: float=0.1, min_w: float=0.1) -> None:
    for k in state:
        avg = state[k]['score'] / max(1, state[k]['use'])
        state[k]['weight'] = (1 - reaction) * state[k]['weight'] + reaction * max(min_w, avg)

def _normalize(w: Dict[str, float]) -> Dict[str, float]:
    total = sum((max(0.0, v) for v in w.values()))
    if total <= 1e-12:
        return {k: 1.0 / len(w) for k in w}
    return {k: max(0.0, v) / total for k, v in w.items()}

def _softmax(u: Dict[str, float], tau: float=1.0) -> Dict[str, float]:
    tau = max(tau, 1e-09)
    m = max(u.values())
    ev = {k: math.exp((v - m) / tau) for k, v in u.items()}
    total = sum(ev.values())
    if total <= 1e-12:
        return {k: 1.0 / len(u) for k in u}
    return {k: v / total for k, v in ev.items()}

def _floor(probs: Dict[str, float], eps: float) -> Dict[str, float]:
    n = len(probs)
    return {k: (1 - eps) * probs[k] + eps / n for k in probs}

def _sample(probs: Dict[str, float]) -> str:
    r, cum = (random.random(), 0.0)
    for k, p in probs.items():
        cum += p
        if r <= cum:
            return k
    return list(probs.keys())[-1]

def _logit_base(state: Dict[str, Dict], cfg: Config) -> Dict[str, float]:
    out = {}
    for k, st in state.items():
        age_n = min(st['age'] / cfg.age_scale, 10.0)
        out[k] = cfg.beta_R * st['recent_reward'] + cfg.beta_A * st['accept_rate'] + cfg.beta_I * st['improve_rate'] - cfg.beta_G * age_n + cfg.beta_V * st['vehicle_saving'] + cfg.beta_C * st['routing_saving'] + cfg.beta_P * st['profit_saving']
    return out

def _unified_utility(state: Dict[str, Dict], cfg: Config) -> Dict[str, float]:
    base = _logit_base(state, cfg)
    rp = _normalize({k: st['weight'] for k, st in state.items()})
    return {k: base[k] + cfg.beta_prob * math.log(rp[k] + 1e-09) for k in state}

def _select(state: Dict[str, Dict], method: str, tau: float, cfg: Config) -> str:
    if method == 'ALNS':
        probs = _normalize({k: st['weight'] for k, st in state.items()})
    elif method == 'unified_logit':
        probs = _floor(_softmax(_unified_utility(state, cfg), tau), cfg.eps_explore)
    else:
        raise ValueError("method must be 'ALNS' or 'unified_logit'")
    return _sample(probs)


_DESTROY_OPS = ['shaw', 'random', 'worst', 'string', 'vehicle_min', 'profit_max', 'cost_min']
_REPAIR_OPS = ['greedy', 'regret2', 'regret3', 'blink', 'random_repair', 'deep_greedy', 'regret4']

def _build_ops(inst: Instance, cfg: Config, max_noise: float):
    destroy_names = cfg.destroy_ops or _DESTROY_OPS
    repair_names = cfg.repair_ops or _REPAIR_OPS
    allow_new = cfg.allow_new_routes
    destroy = {}
    if 'shaw' in destroy_names:
        destroy['shaw'] = lambda s, q: _remove_shaw(s, inst, q, p=6.0)
    if 'random' in destroy_names:
        destroy['random'] = lambda s, q: _remove_random(s, inst, q)
    if 'worst' in destroy_names:
        destroy['worst'] = lambda s, q: _remove_worst(s, inst, q, p=3.0)
    if 'string' in destroy_names:
        destroy['string'] = lambda s, q: _remove_string(s, inst, q, max_len=3)
    if 'vehicle_min' in destroy_names:
        destroy['vehicle_min'] = lambda s, q: _remove_vehicle_min(s, inst, q)
    if 'profit_max' in destroy_names:
        destroy['profit_max'] = lambda s, q: _remove_profit_max(s, inst, q)
    if 'cost_min' in destroy_names:
        destroy['cost_min'] = lambda s, q: _remove_cost_min(s, inst, q)
    repair = {}
    if 'greedy' in repair_names:
        repair['greedy'] = lambda s, n: _repair_greedy(s, inst, n, max_noise, allow_new)
    if 'regret2' in repair_names:
        repair['regret2'] = lambda s, n: _repair_regret(s, inst, 2, n, max_noise, allow_new)
    if 'regret3' in repair_names:
        repair['regret3'] = lambda s, n: _repair_regret(s, inst, 3, n, max_noise, allow_new)
    if 'blink' in repair_names:
        repair['blink'] = lambda s, n: _repair_blink(s, inst, 0.15, allow_new)
    if 'random_repair' in repair_names:
        repair['random_repair'] = lambda s, n: _repair_random(s, inst, allow_new)
    if 'deep_greedy' in repair_names:
        repair['deep_greedy'] = lambda s, n: _repair_deep_greedy(s, inst, n, max_noise, allow_new)
    if 'regret4' in repair_names:
        repair['regret4'] = lambda s, n: _repair_regret(s, inst, 4, n, max_noise, allow_new)
    if not destroy or not repair:
        raise ValueError('At least one destroy and one repair operator are required.')
    return (destroy, repair)

def _run_engine(method: str, inst: Instance, cfg: Config) -> Tuple[Solution, Dict, float]:
    random.seed(cfg.seed)
    maxN = cfg.phi_noise * max((inst.c[i, j] for i in inst.N for j in inst.N if i != j))
    destroy, repair = _build_ops(inst, cfg, maxN)
    noise_ops = {'clean': False, 'noisy': True}
    st_rem = _init_state(list(destroy.keys()))
    st_ins = _init_state(list(repair.keys()))
    st_noise = _init_state(list(noise_ops.keys()))
    cur = _make_empty(inst)
    _start_route(cur, inst.V[0], min(inst.I, key=lambda d: inst.C_depot[d]))
    _start_route(cur, inst.V[1], min(inst.I, key=lambda d: inst.C_depot[d]))
    eval_solution(cur, inst)
    cur = _repair_regret(cur, inst, 2, False, maxN, True)
    eval_solution(cur, inst)
    cur = _prune(cur, inst)
    eval_solution(cur, inst)
    best = cur.copy()
    eval_solution(best, inst)
    cur_cost = -cur.obj
    td = cfg.w_start_pct * max(1.0, abs(cur_cost))
    T = td / math.log(2.0) if td > 0 else 1.0
    visited = {_sol_hash(cur, inst)}
    no_imp = 0
    hist: Dict[str, Any] = {'iter': [], 'best_obj': [], 'cur_obj': [], 'T': [], 'w_rem': {k: [] for k in destroy}, 'w_ins': {k: [] for k in repair}, 'w_noise': {k: [] for k in noise_ops}}
    t0 = time.time()
    for it in range(1, cfg.iters + 1):
        if (it - 1) % cfg.segment == 0:
            _reset_scores(st_rem)
            _reset_scores(st_ins)
            _reset_scores(st_noise)
        tau = max(cfg.tau_min, cfg.tau_init * (1.0 - it / max(1, cfg.iters)) + cfg.tau_min)
        rop = _select(st_rem, method, tau, cfg)
        iop = _select(st_ins, method, tau, cfg)
        nop = _select(st_noise, method, tau, cfg)
        q_max = max(cfg.q_min, min(100, int(cfg.q_max_ratio * len(inst.J))))
        q = random.randint(cfg.q_min, q_max)
        cur_vc = _used_vehicles(cur)
        cur_rc = _routing_cost(cur)
        cur_profit = sum((re.profit for re in cur.evals.values()))
        partial, _ = destroy[rop](cur, q)
        cand = repair[iop](partial, noise_ops[nop])
        eval_solution(cand, inst)
        cand = _prune(cand, inst)
        eval_solution(cand, inst)
        cand_vc = _used_vehicles(cand)
        cand_rc = _routing_cost(cand)
        cand_profit = sum((re.profit for re in cand.evals.values()))
        vsave = max(0.0, cur_vc - cand_vc) / max(1.0, cur_vc)
        rsave = max(0.0, cur_rc - cand_rc) / max(1.0, cur_rc + 1e-09)
        psave = max(0.0, cand_profit - cur_profit) / max(1.0, abs(cur_profit) + 1e-09)
        cand_cost = -cand.obj
        dc = cand_cost - cur_cost
        accept = dc <= 0 or random.random() < math.exp(-dc / max(1e-09, T))
        h = _sol_hash(cand, inst)
        is_new = h not in visited
        if is_new:
            visited.add(h)
        imp_cur = cand.obj > cur.obj + cfg.min_improvement
        imp_best = cand.obj > best.obj + cfg.min_improvement
        reward = 0.0
        if is_new and imp_best:
            reward = cfg.sigma1
        elif is_new and imp_cur:
            reward = cfg.sigma2
        elif is_new and accept and (not imp_cur):
            reward = cfg.sigma3
        imp_flag = imp_cur or imp_best
        if accept:
            cur = cand
            cur_cost = cand_cost
            if imp_best:
                best = cand.copy()
                eval_solution(best, inst)
                no_imp = 0
            else:
                no_imp += 1
        else:
            no_imp += 1
        for st, chosen in ((st_rem, rop), (st_ins, iop), (st_noise, nop)):
            _update_state(st, chosen, reward, accept, imp_flag, vsave, rsave, psave, cfg.sigma1)
        T *= cfg.cooling
        if it % cfg.segment == 0:
            _update_weights(st_rem, cfg.reaction)
            _update_weights(st_ins, cfg.reaction)
            _update_weights(st_noise, cfg.reaction)
        hist['iter'].append(it)
        hist['best_obj'].append(best.obj)
        hist['cur_obj'].append(cur.obj)
        hist['T'].append(T)
        for k in destroy:
            hist['w_rem'][k].append(st_rem[k]['weight'])
        for k in repair:
            hist['w_ins'][k].append(st_ins[k]['weight'])
        for k in noise_ops:
            hist['w_noise'][k].append(st_noise[k]['weight'])
        if no_imp >= cfg.patience:
            print(f'  [{method}] early stop at iter {it} — no improvement in {cfg.patience} iters.')
            break
    runtime = time.time() - t0
    eval_solution(best, inst)
    best = _prune(best, inst)
    eval_solution(best, inst)
    return (best, hist, runtime)

def _build_result(method: str, inst: Instance, seed: int, sol: Solution, hist: Dict, runtime: float) -> Result:
    eval_solution(sol, inst)
    tp = tr = tl = ts = 0.0
    served: Set[int] = set()
    for v in inst.V:
        if v in sol.evals:
            re = sol.evals[v]
            tp += re.profit
            tr += re.distance
            tl += re.lateness_cost
            ts += re.shortage_cost
            served |= {j for j, q in re.delivered.items() if q > 1e-09}
    for j in inst.J:
        if j not in served:
            ts += inst.pi[j] * inst.D[j]
    fc = sum((inst.C_depot[d] for d in sol.opened))
    return Result(method=method, instance_name=inst.name, seed=seed, best_solution=sol, history=hist, runtime_sec=runtime, objective=sol.obj, profit=tp, routing_cost=tr, facility_cost=fc, shortage_penalty=ts, lateness_penalty=tl, opened_depots=sorted(sol.opened), n_used_vehicles=_used_vehicles(sol), n_served_customers=len(served))

def run_alns(inst: Instance, cfg: Optional[Config]=None) -> Result:
    cfg = cfg or Config()
    print(f'\n[ALNS] {inst.name} seed={cfg.seed}')
    sol, hist, rt = _run_engine('ALNS', inst, cfg)
    return _build_result('ALNS', inst, cfg.seed, sol, hist, rt)

def run_unified_logit(inst: Instance, cfg: Optional[Config]=None) -> Result:
    cfg = cfg or Config()
    print(f'\n[Unified Logit] {inst.name} seed={cfg.seed}')
    sol, hist, rt = _run_engine('unified_logit', inst, cfg)
    return _build_result('unified_logit', inst, cfg.seed, sol, hist, rt)

def print_result(result: Result) -> None:
    print(f'\n{result.method} | {result.instance_name} | seed={result.seed}')
    print(f'Objective: {result.objective:.3f}')
    print(f'Profit: {result.profit:.3f}')
    print(f'Routing cost: {result.routing_cost:.3f}')
    print(f'Facility cost: {result.facility_cost:.3f}')
    print(f'Shortage penalty: {result.shortage_penalty:.3f}')
    print(f'Lateness penalty: {result.lateness_penalty:.3f}')
    print(f'Opened depots: {result.opened_depots}')
    print(f'Used vehicles: {result.n_used_vehicles}')
    print(f'Served customers: {result.n_served_customers}')
    print(f'Runtime: {result.runtime_sec:.2f} s')
if __name__ == '__main__':
    DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'R101.txt')
    instance = build_instance_from_file(file_path=DATA_FILE, dataset='R101', n_customers=20, n_depots=3)
    config = Config(seed=7, iters=5000, segment=100, patience=500, cooling=0.99975, destroy_ops=_DESTROY_OPS, repair_ops=_REPAIR_OPS)
    rw_result = run_alns(instance, config)
    ul_result = run_unified_logit(instance, config)
    print_result(rw_result)
    print_result(ul_result)
