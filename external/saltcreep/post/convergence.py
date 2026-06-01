"""Lame convergence study for the implemented axisymmetric elements.

The script assembles the elastic hollow-cylinder problem used by the C++ tests,
computes the relative error in u_r(Ri), and writes:

  results/convergence/lame_convergence.csv
  results/convergence/lame_error_vs_dofs.png
  results/convergence/lame_error_vs_time.png

Usage:
    python post/convergence.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
import csv
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve


RI = 1.0
RE = 3.0
HEIGHT = 1.0
E = 25.0e9
NU = 0.30
P_INNER = 1.0e6
OUT_DIR = Path("results/convergence")
GL2_A = 1.0 / math.sqrt(3.0)
GL3_A = math.sqrt(3.0 / 5.0)
GL3_POINTS = (-GL3_A, 0.0, GL3_A)
GL3_WEIGHTS = (5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0)


@dataclass(frozen=True)
class GaussPoint:
    xi: float
    weight: float
    eta: float = 0.0


@dataclass
class Mesh:
    nodes: np.ndarray
    conn: list[list[int]]
    dofs_per_node: int

    @property
    def total_dofs(self) -> int:
        return self.nodes.shape[0] * self.dofs_per_node

    def dof_index(self, node_id: int, local_dof: int) -> int:
        return node_id * self.dofs_per_node + local_dof


class Element:
    name: str
    n_nodes: int
    dofs_per_node: int
    gauss: list[GaussPoint]

    def shape(self, gp: GaussPoint) -> np.ndarray:
        raise NotImplementedError

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError

    def b_matrix(self, gp: GaussPoint, coords: np.ndarray) -> np.ndarray:
        n = self.shape(gp)
        dxi, deta = self.dshape(gp)
        if self.dofs_per_node == 1:
            r = float(n @ coords[:, 0])
            jac = float(dxi @ coords[:, 0])
            b = np.zeros((4, self.n_nodes))
            b[0, :] = dxi / jac
            b[1, :] = n / r
            return b

        r = float(n @ coords[:, 0])
        dr_dxi = float(dxi @ coords[:, 0])
        dr_deta = float(deta @ coords[:, 0])
        dz_dxi = float(dxi @ coords[:, 1])
        dz_deta = float(deta @ coords[:, 1])
        detj = dr_dxi * dz_deta - dr_deta * dz_dxi

        b = np.zeros((4, self.n_nodes * 2))
        for i in range(self.n_nodes):
            dn_dr = (dz_deta * dxi[i] - dz_dxi * deta[i]) / detj
            dn_dz = (-dr_deta * dxi[i] + dr_dxi * deta[i]) / detj
            col_r = 2 * i
            col_z = col_r + 1
            b[0, col_r] = dn_dr
            b[1, col_r] = n[i] / r
            b[2, col_z] = dn_dz
            b[3, col_r] = dn_dz
            b[3, col_z] = dn_dr
        return b

    def jacobian_weight(self, gp: GaussPoint, coords: np.ndarray) -> float:
        n = self.shape(gp)
        dxi, deta = self.dshape(gp)
        r = float(n @ coords[:, 0])
        if self.dofs_per_node == 1:
            jac = float(dxi @ coords[:, 0])
            return 2.0 * math.pi * r * abs(jac) * gp.weight

        dr_dxi = float(dxi @ coords[:, 0])
        dr_deta = float(deta @ coords[:, 0])
        dz_dxi = float(dxi @ coords[:, 1])
        dz_deta = float(deta @ coords[:, 1])
        detj = dr_dxi * dz_deta - dr_deta * dz_dxi
        return 2.0 * math.pi * r * abs(detj) * gp.weight


class L3(Element):
    name = "L3"
    n_nodes = 3
    dofs_per_node = 1
    gauss = [
        GaussPoint(-GL3_A, 5.0 / 9.0),
        GaussPoint(0.0, 8.0 / 9.0),
        GaussPoint(GL3_A, 5.0 / 9.0),
    ]

    def shape(self, gp: GaussPoint) -> np.ndarray:
        x = gp.xi
        return np.array([0.5 * x * (x - 1.0), 1.0 - x * x, 0.5 * x * (x + 1.0)])

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        x = gp.xi
        return np.array([x - 0.5, -2.0 * x, x + 0.5]), np.zeros(3)


class Q4(Element):
    name = "Q4"
    n_nodes = 4
    dofs_per_node = 2
    gauss = [GaussPoint(x, 1.0, e) for e in (-GL2_A, GL2_A) for x in (-GL2_A, GL2_A)]

    def shape(self, gp: GaussPoint) -> np.ndarray:
        x, e = gp.xi, gp.eta
        return 0.25 * np.array([
            (1 - x) * (1 - e),
            (1 + x) * (1 - e),
            (1 + x) * (1 + e),
            (1 - x) * (1 + e),
        ])

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        x, e = gp.xi, gp.eta
        dxi = 0.25 * np.array([-(1 - e), (1 - e), (1 + e), -(1 + e)])
        deta = 0.25 * np.array([-(1 - x), -(1 + x), (1 + x), (1 - x)])
        return dxi, deta


class T3(Element):
    name = "T3"
    n_nodes = 3
    dofs_per_node = 2
    gauss = [
        GaussPoint(1.0 / 6.0, 1.0 / 6.0, 1.0 / 6.0),
        GaussPoint(2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        GaussPoint(1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    ]

    def shape(self, gp: GaussPoint) -> np.ndarray:
        return np.array([1.0 - gp.xi - gp.eta, gp.xi, gp.eta])

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        return np.array([-1.0, 1.0, 0.0]), np.array([-1.0, 0.0, 1.0])


class Q8(Element):
    name = "Q8"
    n_nodes = 8
    dofs_per_node = 2
    gauss = [GaussPoint(x, wx * we, e)
             for e, we in zip(GL3_POINTS, GL3_WEIGHTS)
             for x, wx in zip(GL3_POINTS, GL3_WEIGHTS)]

    def shape(self, gp: GaussPoint) -> np.ndarray:
        x, e = gp.xi, gp.eta
        return np.array([
            -0.25 * (1 - x) * (1 - e) * (1 + x + e),
            -0.25 * (1 + x) * (1 - e) * (1 - x + e),
            -0.25 * (1 + x) * (1 + e) * (1 - x - e),
            -0.25 * (1 - x) * (1 + e) * (1 + x - e),
            0.5 * (1 - x * x) * (1 - e),
            0.5 * (1 + x) * (1 - e * e),
            0.5 * (1 - x * x) * (1 + e),
            0.5 * (1 - x) * (1 - e * e),
        ])

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        x, e = gp.xi, gp.eta
        dxi = np.array([
            0.25 * (1 - e) * (2 * x + e),
            0.25 * (1 - e) * (2 * x - e),
            0.25 * (1 + e) * (2 * x + e),
            0.25 * (1 + e) * (2 * x - e),
            -x * (1 - e),
            0.5 * (1 - e * e),
            -x * (1 + e),
            -0.5 * (1 - e * e),
        ])
        deta = np.array([
            0.25 * (1 - x) * (x + 2 * e),
            0.25 * (1 + x) * (-x + 2 * e),
            0.25 * (1 + x) * (x + 2 * e),
            0.25 * (1 - x) * (-x + 2 * e),
            -0.5 * (1 - x * x),
            -(1 + x) * e,
            0.5 * (1 - x * x),
            -(1 - x) * e,
        ])
        return dxi, deta


class Q9(Element):
    name = "Q9"
    n_nodes = 9
    dofs_per_node = 2
    gauss = [GaussPoint(x, wx * we, e)
             for e, we in zip(GL3_POINTS, GL3_WEIGHTS)
             for x, wx in zip(GL3_POINTS, GL3_WEIGHTS)]

    @staticmethod
    def lagrange(s: float) -> tuple[float, float, float, float, float, float]:
        return (
            0.5 * s * (s - 1.0),
            1.0 - s * s,
            0.5 * s * (s + 1.0),
            s - 0.5,
            -2.0 * s,
            s + 0.5,
        )

    def shape(self, gp: GaussPoint) -> np.ndarray:
        xm, x0, xp, *_ = self.lagrange(gp.xi)
        em, e0, ep, *_ = self.lagrange(gp.eta)
        return np.array([xm * em, xp * em, xp * ep, xm * ep, x0 * em,
                         xp * e0, x0 * ep, xm * e0, x0 * e0])

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        xm, x0, xp, dxm, dx0, dxp = self.lagrange(gp.xi)
        em, e0, ep, dem, de0, dep = self.lagrange(gp.eta)
        dxi = np.array([dxm * em, dxp * em, dxp * ep, dxm * ep, dx0 * em,
                        dxp * e0, dx0 * ep, dxm * e0, dx0 * e0])
        deta = np.array([xm * dem, xp * dem, xp * dep, xm * dep, x0 * dem,
                         xp * de0, x0 * dep, xm * de0, x0 * de0])
        return dxi, deta


class AQ9(Element):
    name = "AQ9"
    n_nodes = 9
    dofs_per_node = 2
    gauss = [GaussPoint(-100.0 - i, we, e)
             for e, we in zip(GL3_POINTS, GL3_WEIGHTS)
             for i in range(4)]

    @staticmethod
    def _bounds(coords: np.ndarray) -> tuple[float, float, float]:
        r_l = float(np.min(coords[:, 0]))
        r_r = float(np.max(coords[:, 0]))
        if r_l <= 0.0 or r_r <= r_l:
            raise ValueError("AQ9 invalid radial bounds")
        return r_l, 0.5 * (r_l + r_r), r_r

    @staticmethod
    def _radial_quadrature(ct: float) -> tuple[np.ndarray, np.ndarray]:
        y = np.array([1.20, 1.50, 1.85, 0.08, 0.30, 0.40, 0.22], dtype=float)

        def poly_moment(m: int) -> float:
            return (2.0 ** (m + 1) - 1.0) / (m + 1)

        def recip_moment(k: int) -> float:
            if k == 1:
                return math.log((2.0 - ct) / (1.0 - ct))
            if k == 2:
                return 1.0 / (1.0 - ct) - 1.0 / (2.0 - ct)
            return 0.5 * ((1.0 - ct) ** -2 - (2.0 - ct) ** -2)

        def valid(v: np.ndarray) -> bool:
            return (1.0 < v[0] < v[1] < v[2] < 2.0 and np.all(v[3:] > 0.0))

        converged = False
        for _ in range(80):
            x = np.array([1.0, y[0], y[1], y[2]])
            w = np.array([y[3], y[4], y[5], y[6]])
            res = np.zeros(7)
            jac = np.zeros((7, 7))
            for m in range(4):
                res[m] = float(np.sum(w * x ** m)) - poly_moment(m)
                for j in range(1, 4):
                    jac[m, j - 1] = 0.0 if m == 0 else w[j] * m * x[j] ** (m - 1)
                for j in range(4):
                    jac[m, 3 + j] = x[j] ** m
            for k in range(1, 4):
                row = 3 + k
                res[row] = float(np.sum(w / (x - ct) ** k)) - recip_moment(k)
                for j in range(1, 4):
                    jac[row, j - 1] = -k * w[j] / (x[j] - ct) ** (k + 1)
                for j in range(4):
                    jac[row, 3 + j] = 1.0 / (x[j] - ct) ** k
            if np.linalg.norm(res, ord=np.inf) < 1.0e-13:
                converged = True
                break
            delta = np.linalg.solve(jac, -res)
            alpha = 1.0
            while alpha > 1.0e-9:
                trial = y + alpha * delta
                if valid(trial):
                    y = trial
                    break
                alpha *= 0.5
            else:
                raise ValueError("AQ9 radial quadrature failed")

        if not converged:
            raise ValueError("AQ9 radial quadrature did not converge")

        weights = np.array([y[3], y[4], y[5], y[6]])
        if np.any(weights <= 0.0):
            raise ValueError(f"AQ9 radial quadrature produced non-positive weights for ct={ct}")
        return np.array([1.0, y[0], y[1], y[2]]), weights

    @staticmethod
    def _xi(gp: GaussPoint, coords: np.ndarray) -> tuple[float, float]:
        if gp.xi <= -100.0:
            idx = int(round(-(gp.xi + 100.0)))
            r_l, _, r_r = AQ9._bounds(coords)
            ct = 1.0 - r_l / (r_r - r_l)
            xi, weights = AQ9._radial_quadrature(ct)
            return float(xi[idx]), float(weights[idx] * gp.weight)
        if -1.0 <= gp.xi <= 1.0:
            return 1.5 + 0.5 * gp.xi, gp.weight
        return gp.xi, gp.weight

    @staticmethod
    def _eta_basis(eta: float) -> tuple[np.ndarray, np.ndarray]:
        return (
            np.array([0.5 * eta * (eta - 1.0), 1.0 - eta * eta, 0.5 * eta * (eta + 1.0)]),
            np.array([eta - 0.5, -2.0 * eta, eta + 0.5]),
        )

    @staticmethod
    def _radial_basis(coords: np.ndarray, xi: float) -> tuple[np.ndarray, np.ndarray]:
        r_l, r_m, r_r = AQ9._bounds(coords)
        dr_dxi = r_r - r_l
        r = r_l + (xi - 1.0) * dr_dxi
        a = np.array([[1.0, r_l, 1.0 / r_l],
                      [1.0, r_m, 1.0 / r_m],
                      [1.0, r_r, 1.0 / r_r]])
        coeff = np.linalg.inv(a)
        p = np.array([1.0, r, 1.0 / r])
        dp = np.array([0.0, dr_dxi, -dr_dxi / (r * r)])
        return p @ coeff, dp @ coeff

    def _shape_coords(self, gp: GaussPoint, coords: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        xi, weight = self._xi(gp, coords)
        r, dr = self._radial_basis(coords, xi)
        e, de = self._eta_basis(gp.eta)
        n = np.array([r[0] * e[0], r[2] * e[0], r[2] * e[2], r[0] * e[2],
                      r[1] * e[0], r[2] * e[1], r[1] * e[2], r[0] * e[1],
                      r[1] * e[1]])
        dxi = np.array([dr[0] * e[0], dr[2] * e[0], dr[2] * e[2], dr[0] * e[2],
                        dr[1] * e[0], dr[2] * e[1], dr[1] * e[2], dr[0] * e[1],
                        dr[1] * e[1]])
        deta = np.array([r[0] * de[0], r[2] * de[0], r[2] * de[2], r[0] * de[2],
                         r[1] * de[0], r[2] * de[1], r[1] * de[2], r[0] * de[1],
                         r[1] * de[1]])
        return n, dxi, deta, weight

    def shape(self, gp: GaussPoint) -> np.ndarray:
        coords = np.array([[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0],
                           [1.5, 0.0], [2.0, 0.5], [1.5, 1.0], [1.0, 0.5],
                           [1.5, 0.5]])
        n, _, _, _ = self._shape_coords(gp, coords)
        return n

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        coords = np.array([[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0],
                           [1.5, 0.0], [2.0, 0.5], [1.5, 1.0], [1.0, 0.5],
                           [1.5, 0.5]])
        _, dxi, deta, _ = self._shape_coords(gp, coords)
        return dxi, deta

    def b_matrix(self, gp: GaussPoint, coords: np.ndarray) -> np.ndarray:
        n, dxi, deta, _ = self._shape_coords(gp, coords)
        r = float(n @ coords[:, 0])
        dr_dxi = float(dxi @ coords[:, 0])
        dr_deta = float(deta @ coords[:, 0])
        dz_dxi = float(dxi @ coords[:, 1])
        dz_deta = float(deta @ coords[:, 1])
        detj = dr_dxi * dz_deta - dr_deta * dz_dxi
        b = np.zeros((4, self.n_nodes * 2))
        for i in range(self.n_nodes):
            dn_dr = (dz_deta * dxi[i] - dz_dxi * deta[i]) / detj
            dn_dz = (-dr_deta * dxi[i] + dr_dxi * deta[i]) / detj
            col_r = 2 * i
            col_z = col_r + 1
            b[0, col_r] = dn_dr
            b[1, col_r] = n[i] / r
            b[2, col_z] = dn_dz
            b[3, col_r] = dn_dz
            b[3, col_z] = dn_dr
        return b

    def jacobian_weight(self, gp: GaussPoint, coords: np.ndarray) -> float:
        n, dxi, deta, weight = self._shape_coords(gp, coords)
        r = float(n @ coords[:, 0])
        dr_dxi = float(dxi @ coords[:, 0])
        dr_deta = float(deta @ coords[:, 0])
        dz_dxi = float(dxi @ coords[:, 1])
        dz_deta = float(deta @ coords[:, 1])
        detj = dr_dxi * dz_deta - dr_deta * dz_dxi
        return 2.0 * math.pi * r * abs(detj) * weight


class T6(Element):
    name = "T6"
    n_nodes = 6
    dofs_per_node = 2
    a = 0.816847572980459
    b = 0.091576213509771
    c = 0.108103018168070
    d = 0.445948490915965
    w1 = 0.054975871827661
    w2 = 0.111690794839006
    gauss = [
        GaussPoint(b, w1, b), GaussPoint(a, w1, b), GaussPoint(b, w1, a),
        GaussPoint(d, w2, d), GaussPoint(c, w2, d), GaussPoint(d, w2, c),
    ]

    def shape(self, gp: GaussPoint) -> np.ndarray:
        l1 = 1.0 - gp.xi - gp.eta
        l2 = gp.xi
        l3 = gp.eta
        return np.array([
            l1 * (2.0 * l1 - 1.0),
            l2 * (2.0 * l2 - 1.0),
            l3 * (2.0 * l3 - 1.0),
            4.0 * l1 * l2,
            4.0 * l2 * l3,
            4.0 * l3 * l1,
        ])

    def dshape(self, gp: GaussPoint) -> tuple[np.ndarray, np.ndarray]:
        l1 = 1.0 - gp.xi - gp.eta
        l2 = gp.xi
        l3 = gp.eta
        dxi = np.array([-(4 * l1 - 1), 4 * l2 - 1, 0.0, 4 * (l1 - l2), 4 * l3, -4 * l3])
        deta = np.array([-(4 * l1 - 1), 0.0, 4 * l3 - 1, -4 * l2, 4 * l2, 4 * (l1 - l3)])
        return dxi, deta


def elastic_d() -> np.ndarray:
    denom = (1.0 + NU) * (1.0 - 2.0 * NU)
    c1 = E * (1.0 - NU) / denom
    c2 = E * NU / denom
    c3 = E / (2.0 * (1.0 + NU))
    return np.array([
        [c1, c2, c2, 0.0],
        [c2, c1, c2, 0.0],
        [c2, c2, c1, 0.0],
        [0.0, 0.0, 0.0, c3],
    ])


def lame_ur(r: float) -> float:
    a = P_INNER * RI * RI / (RE * RE - RI * RI)
    b = P_INNER * RI * RI * RE * RE / (RE * RE - RI * RI)
    return (1.0 + NU) / E * ((1.0 - 2.0 * NU) * a * r + b / r)


def edge_nodes(n: int, ratio: float = 1.0) -> list[float]:
    if abs(ratio - 1.0) < 1.0e-12:
        return [RI + (RE - RI) * i / n for i in range(n + 1)]
    q = ratio ** (1.0 / (n - 1))
    h0 = (RE - RI) * (q - 1.0) / (q ** n - 1.0)
    radii = [RI]
    r = RI
    for i in range(n):
        r += h0 * q ** i
        radii.append(r)
    radii[-1] = RE
    return radii


def build_l3(n_radial: int) -> Mesh:
    edges = edge_nodes(n_radial)
    radii: list[float] = []
    for i in range(n_radial):
        radii.extend([edges[i], 0.5 * (edges[i] + edges[i + 1])])
    radii.append(RE)
    conn = [[2 * i, 2 * i + 1, 2 * i + 2] for i in range(n_radial)]
    nodes = np.array([[r, 0.0] for r in radii])
    return Mesh(nodes, conn, 1)


def build_q4(n_radial: int, n_axial: int) -> Mesh:
    radii = edge_nodes(n_radial)
    nodes = np.array([[r, HEIGHT * iz / n_axial]
                      for iz in range(n_axial + 1) for r in radii])
    def node_id(ir: int, iz: int) -> int:
        return iz * (n_radial + 1) + ir
    conn = []
    for iz in range(n_axial):
        for ir in range(n_radial):
            conn.append([node_id(ir, iz), node_id(ir + 1, iz),
                         node_id(ir + 1, iz + 1), node_id(ir, iz + 1)])
    return Mesh(nodes, conn, 2)


def build_q9(n_radial: int, n_axial: int, serendipity: bool = False) -> Mesh:
    edges = edge_nodes(n_radial)
    fine_r: list[float] = []
    for i in range(n_radial):
        fine_r.extend([edges[i], 0.5 * (edges[i] + edges[i + 1])])
    fine_r.append(RE)
    nr = 2 * n_radial
    nz = 2 * n_axial
    nodes: list[tuple[float, float]] = []
    ids: dict[tuple[int, int], int] = {}
    for iz in range(nz + 1):
        for ir in range(nr + 1):
            if serendipity and ir % 2 == 1 and iz % 2 == 1:
                continue
            ids[(ir, iz)] = len(nodes)
            nodes.append((fine_r[ir], HEIGHT * iz / nz))
    conn = []
    for iz in range(n_axial):
        for ir in range(n_radial):
            i, j = 2 * ir, 2 * iz
            base = [ids[(i, j)], ids[(i + 2, j)], ids[(i + 2, j + 2)], ids[(i, j + 2)],
                    ids[(i + 1, j)], ids[(i + 2, j + 1)], ids[(i + 1, j + 2)],
                    ids[(i, j + 1)]]
            if not serendipity:
                base.append(ids[(i + 1, j + 1)])
            conn.append(base)
    return Mesh(np.array(nodes), conn, 2)


def build_t3(n_radial: int, n_axial: int) -> Mesh:
    mesh = build_q4(n_radial, n_axial)
    conn = []
    for iz in range(n_axial):
        for ir in range(n_radial):
            n00 = iz * (n_radial + 1) + ir
            n10 = n00 + 1
            n01 = (iz + 1) * (n_radial + 1) + ir
            n11 = n01 + 1
            conn.append([n00, n10, n11])
            conn.append([n00, n11, n01])
    return Mesh(mesh.nodes, conn, 2)


def build_t6(n_radial: int, n_axial: int) -> Mesh:
    mesh = build_q9(n_radial, n_axial)
    nr = 2 * n_radial
    def node_id(ir: int, iz: int) -> int:
        return iz * (nr + 1) + ir
    conn = []
    for iz in range(n_axial):
        for ir in range(n_radial):
            i, j = 2 * ir, 2 * iz
            conn.append([node_id(i, j), node_id(i + 2, j), node_id(i + 2, j + 2),
                         node_id(i + 1, j), node_id(i + 2, j + 1), node_id(i + 1, j + 1)])
            conn.append([node_id(i, j), node_id(i + 2, j + 2), node_id(i, j + 2),
                         node_id(i + 1, j + 1), node_id(i + 1, j + 2), node_id(i, j + 1)])
    return Mesh(mesh.nodes, conn, 2)


def assemble_k(mesh: Mesh, elem: Element) -> csr_matrix:
    d = elastic_d()
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    for element_nodes in mesh.conn:
        coords = mesh.nodes[element_nodes]
        local_dofs = [mesh.dof_index(node, dof)
                      for node in element_nodes for dof in range(mesh.dofs_per_node)]
        ke = np.zeros((len(local_dofs), len(local_dofs)))
        for gp in elem.gauss:
            b = elem.b_matrix(gp, coords)
            ke += b.T @ d @ b * elem.jacobian_weight(gp, coords)
        for i, gi in enumerate(local_dofs):
            for j, gj in enumerate(local_dofs):
                rows.append(gi)
                cols.append(gj)
                vals.append(float(ke[i, j]))
    return coo_matrix((vals, (rows, cols)), shape=(mesh.total_dofs, mesh.total_dofs)).tocsr()


def pressure_load(mesh: Mesh, elem: Element, n_radial: int, n_axial: int) -> np.ndarray:
    f = np.zeros(mesh.total_dofs)
    if elem.dofs_per_node == 1:
        f[0] = P_INNER * 2.0 * math.pi * RI
        return f

    if elem.name == "Q4":
        a = 1.0 / math.sqrt(3.0)
        for iz in range(n_axial):
            eid = iz * n_radial
            coords = mesh.nodes[mesh.conn[eid]]
            for eta in (-a, a):
                gp = GaussPoint(-1.0, 1.0, eta)
                n = elem.shape(gp)
                _, dn_eta = elem.dshape(gp)
                r_gp = float(n @ coords[:, 0])
                dz_deta = float(dn_eta @ coords[:, 1])
                w = 2.0 * math.pi * r_gp * abs(dz_deta)
                for local in (0, 3):
                    f[mesh.dof_index(mesh.conn[eid][local], 0)] += n[local] * P_INNER * w
        return f

    if elem.name == "T3":
        a = 1.0 / math.sqrt(3.0)
        for iz in range(n_axial):
            eid = 2 * (iz * n_radial) + 1
            coords = mesh.nodes[mesh.conn[eid]]
            for s in (-a, a):
                n0 = 0.5 * (1.0 - s)
                n2 = 0.5 * (1.0 + s)
                r_gp = n0 * coords[0, 0] + n2 * coords[2, 0]
                dz_ds = 0.5 * (coords[2, 1] - coords[0, 1])
                w = 2.0 * math.pi * r_gp * abs(dz_ds)
                for local, nval in ((0, n0), (2, n2)):
                    f[mesh.dof_index(mesh.conn[eid][local], 0)] += nval * P_INNER * w
        return f

    if elem.name in {"Q8", "Q9", "AQ9"}:
        a = math.sqrt(3.0 / 5.0)
        points = (-a, 0.0, a)
        weights = (5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0)
        for iz in range(n_axial):
            eid = iz * n_radial
            coords = mesh.nodes[mesh.conn[eid]]
            for eta, weight in zip(points, weights):
                gp = GaussPoint(-1.0, weight, eta)
                if isinstance(elem, AQ9):
                    n, _, dn_eta, _ = elem._shape_coords(gp, coords)
                else:
                    n = elem.shape(gp)
                    _, dn_eta = elem.dshape(gp)
                r_gp = float(n @ coords[:, 0])
                dr_deta = float(dn_eta @ coords[:, 0])
                dz_deta = float(dn_eta @ coords[:, 1])
                w = 2.0 * math.pi * r_gp * math.hypot(dr_deta, dz_deta) * weight
                for local in (0, 3, 7):
                    f[mesh.dof_index(mesh.conn[eid][local], 0)] += n[local] * P_INNER * w
        return f

    if elem.name == "T6":
        a = math.sqrt(3.0 / 5.0)
        points = (-a, 0.0, a)
        weights = (5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0)
        for iz in range(n_axial):
            eid = 2 * (iz * n_radial) + 1
            coords = mesh.nodes[mesh.conn[eid]]
            for s, weight in zip(points, weights):
                gp = GaussPoint(0.0, weight, 0.5 * (1.0 + s))
                n = elem.shape(gp)
                _, dn_eta = elem.dshape(gp)
                r_gp = float(n @ coords[:, 0])
                dr_deta = float(dn_eta @ coords[:, 0])
                dz_deta = float(dn_eta @ coords[:, 1])
                w = 2.0 * math.pi * r_gp * 0.5 * math.hypot(dr_deta, dz_deta) * weight
                for local in (0, 2, 5):
                    f[mesh.dof_index(mesh.conn[eid][local], 0)] += n[local] * P_INNER * w
        return f

    raise ValueError(elem.name)


def solve_lame(mesh: Mesh, elem: Element, n_radial: int, n_axial: int) -> np.ndarray:
    k = assemble_k(mesh, elem)
    f = pressure_load(mesh, elem, n_radial, n_axial)
    if elem.dofs_per_node == 1:
        return spsolve(k, f)

    prescribed: dict[int, float] = {}
    for node_id, (r, _) in enumerate(mesh.nodes):
        prescribed[mesh.dof_index(node_id, 1)] = 0.0
        if abs(r - RE) < 1.0e-12:
            prescribed[mesh.dof_index(node_id, 0)] = lame_ur(RE)

    all_dofs = np.arange(mesh.total_dofs)
    fixed = np.array(sorted(prescribed))
    free = np.setdiff1d(all_dofs, fixed, assume_unique=True)
    u_fixed = np.array([prescribed[int(d)] for d in fixed])
    rhs = f[free] - k[free][:, fixed] @ u_fixed
    u = np.zeros(mesh.total_dofs)
    u[fixed] = u_fixed
    u[free] = spsolve(k[free][:, free], rhs)
    return u


def build_case(name: str, n_radial: int) -> tuple[Element, Mesh, int]:
    if name == "L3":
        return L3(), build_l3(n_radial), 1
    n_axial = max(2, n_radial // 2)
    if name == "AQ9":
        n_axial = 1
    if name == "T3":
        n_axial = n_radial
    builders = {
        "Q4": (Q4(), build_q4),
        "T3": (T3(), build_t3),
        "Q8": (Q8(), lambda nr, na: build_q9(nr, na, serendipity=True)),
        "Q9": (Q9(), build_q9),
        "AQ9": (AQ9(), build_q9),
        "T6": (T6(), build_t6),
    }
    elem, builder = builders[name]
    return elem, builder(n_radial, n_axial), n_axial


def run() -> list[dict[str, float | str | int]]:
    schedules = {
        "L3": [5, 10, 20, 40],
        "Q4": [5, 10, 20, 40],
        "T3": [5, 10, 20, 40],
        "Q8": [3, 6, 12, 24],
        "Q9": [3, 6, 12, 24],
        "AQ9": [1, 2, 4],
        "T6": [3, 6, 12, 24],
    }
    rows: list[dict[str, float | str | int]] = []
    exact = lame_ur(RI)
    for name, meshes in schedules.items():
        for n_radial in meshes:
            elem, mesh, n_axial = build_case(name, n_radial)
            t0 = perf_counter()
            u = solve_lame(mesh, elem, n_radial, n_axial)
            elapsed = perf_counter() - t0
            if elem.dofs_per_node == 1:
                u_inner = float(u[0])
            else:
                inner = [mesh.dof_index(i, 0) for i, node in enumerate(mesh.nodes)
                         if abs(node[0] - RI) < 1.0e-12]
                u_inner = float(np.mean(u[inner]))
            rows.append({
                "element": name,
                "n_radial": n_radial,
                "n_axial": n_axial,
                "dofs": mesh.total_dofs,
                "error": abs(u_inner - exact) / abs(exact),
                "time_s": elapsed,
            })
            print(f"{name:>2} n={n_radial:<2} dofs={mesh.total_dofs:<5} "
                  f"err={rows[-1]['error']:.3e} time={elapsed:.3f}s")
    return rows


def rate(values: list[float]) -> float:
    rates = [math.log(values[i] / values[i + 1], 2.0)
             for i in range(len(values) - 1) if values[i + 1] > 1.0e-15]
    return min(rates) if rates else float("nan")


def write_outputs(rows: list[dict[str, float | str | int]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "lame_convergence.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["element", "n_radial", "n_axial", "dofs", "error", "time_s"])
        writer.writeheader()
        writer.writerows(rows)

    for ykey, ylabel, filename in [
        ("dofs", "Graus de liberdade", "lame_error_vs_dofs.png"),
        ("time_s", "Tempo de montagem+solucao (s)", "lame_error_vs_time.png"),
    ]:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for name in ("L3", "Q4", "T3", "Q8", "Q9", "AQ9", "T6"):
            data = [r for r in rows if r["element"] == name]
            x = [float(r[ykey]) for r in data]
            y = [float(r["error"]) for r in data]
            ax.loglog(x, y, marker="o", label=name)
        ax.set_xlabel(ylabel)
        ax.set_ylabel("Erro relativo em u_r(Ri)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT_DIR / filename, dpi=160)

    print(f"Wrote {csv_path}")
    for name in ("L3", "Q4", "T3", "Q8", "Q9", "AQ9", "T6"):
        errors = [float(r["error"]) for r in rows if r["element"] == name]
        print(f"{name:>2} min_rate={rate(errors):.2f} final_error={errors[-1]:.3e}")


def main() -> None:
    write_outputs(run())


if __name__ == "__main__":
    main()
