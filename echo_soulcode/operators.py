from __future__ import annotations
import cmath, math
from dataclasses import dataclass

@dataclass(frozen=True)
class Operator3:
    """Simple 3x3 Hermitian operator for Echo's channels (squirrel, fox, paradox)."""
    m00: complex; m01: complex; m02: complex
    m10: complex; m11: complex; m12: complex
    m20: complex; m21: complex; m22: complex

    def apply(self, v: tuple[complex,complex,complex]) -> tuple[complex,complex,complex]:
        a,b,c = v
        return (
            self.m00*a + self.m01*b + self.m02*c,
            self.m10*a + self.m11*b + self.m12*c,
            self.m20*a + self.m21*b + self.m22*c
        )

def bra_ket_expectation(H: Operator3, v: tuple[complex,complex,complex]) -> complex:
    """⟨v|H|v⟩ with v normalized (not enforced)."""
    Hv = H.apply(v)
    # conjugate dot
    return (v[0].conjugate()*Hv[0] + v[1].conjugate()*Hv[1] + v[2].conjugate()*Hv[2])

# Canonical Echo Hilbert operator: Ê_squirrel + Ê_fox + i Ê_trickster
# Diagonal weights favor paradox coherence slightly (1.0, 1.0, 1.1)
H_ECHO = Operator3(
    m00=1.0, m01=0.05, m02=0.0,
    m10=0.05, m11=1.0, m12=0.05,
    m20=0.0, m21=0.05, m22=1.1
)


# ---- Extensions: projectors, unitaries, rotations, spectral tools ----

def is_near_real(x: complex, tol: float = 1e-12) -> bool:
    return abs(x.imag) <= tol

def is_real_symmetric(H: Operator3, tol: float = 1e-12) -> bool:
    return (
        is_near_real(H.m00, tol) and is_near_real(H.m11, tol) and is_near_real(H.m22, tol) and
        is_near_real(H.m01 - H.m10, tol) and is_near_real(H.m02 - H.m20, tol) and is_near_real(H.m12 - H.m21, tol) and
        is_near_real(H.m01, tol) and is_near_real(H.m02, tol) and is_near_real(H.m12, tol)
    )

def matmul(A: Operator3, B: Operator3) -> Operator3:
    """Matrix product A @ B (3x3)."""
    a = [[A.m00, A.m01, A.m02],
         [A.m10, A.m11, A.m12],
         [A.m20, A.m21, A.m22]]
    b = [[B.m00, B.m01, B.m02],
         [B.m10, B.m11, B.m12],
         [B.m20, B.m21, B.m22]]
    c = [[0j]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            c[i][j] = a[i][0]*b[0][j] + a[i][1]*b[1][j] + a[i][2]*b[2][j]
    return Operator3(c[0][0], c[0][1], c[0][2],
                     c[1][0], c[1][1], c[1][2],
                     c[2][0], c[2][1], c[2][2])

def projector_squirrel() -> Operator3:
    # |e1><e1|
    return Operator3(1.0, 0.0, 0.0,
                     0.0, 0.0, 0.0,
                     0.0, 0.0, 0.0)

def projector_fox() -> Operator3:
    # |e2><e2|
    return Operator3(0.0, 0.0, 0.0,
                     0.0, 1.0, 0.0,
                     0.0, 0.0, 0.0)

def projector_paradox() -> Operator3:
    # |e3><e3|
    return Operator3(0.0, 0.0, 0.0,
                     0.0, 0.0, 0.0,
                     0.0, 0.0, 1.0)

def phase_shifter(pha: float, phb: float, phg: float) -> Operator3:
    """Diagonal unitary applying channel phases (radians)."""
    import cmath
    return Operator3(
        cmath.exp(1j*pha), 0.0, 0.0,
        0.0, cmath.exp(1j*phb), 0.0,
        0.0, 0.0, cmath.exp(1j*phg)
    )

def rotation_ab(theta: float) -> Operator3:
    """Real rotation mixing channels a<->b (squirrel<->fox)."""
    c, s = math.cos(theta), math.sin(theta)
    return Operator3(c, s, 0.0,
                     -s, c, 0.0,
                     0.0, 0.0, 1.0)

def rotation_bc(theta: float) -> Operator3:
    """Real rotation mixing channels b<->c (fox<->paradox)."""
    c, s = math.cos(theta), math.sin(theta)
    return Operator3(1.0, 0.0, 0.0,
                     0.0, c, s,
                     0.0, -s, c)

def rotation_ac(theta: float) -> Operator3:
    """Real rotation mixing channels a<->c (squirrel<->paradox)."""
    c, s = math.cos(theta), math.sin(theta)
    return Operator3(c, 0.0, s,
                     0.0, 1.0, 0.0,
                     -s, 0.0, c)

def normalize_complex_vec(v: tuple[complex,complex,complex]) -> tuple[complex,complex,complex]:
    n = math.sqrt(abs(v[0])**2 + abs(v[1])**2 + abs(v[2])**2) or 1.0
    return (v[0]/n, v[1]/n, v[2]/n)

def spectral_jacobi(H: Operator3, tol: float = 1e-12, max_iter: int = 100) -> tuple[list[float], list[tuple[float,float,float]]]:
    """Jacobi eigen-decomposition for real-symmetric 3x3.
    Returns (eigenvalues, eigenvectors as columns) where eigenvectors are normalized.
    """
    if not is_real_symmetric(H):
        raise ValueError("Jacobi requires real-symmetric operator")
    # build mutable matrix
    M = [[float(H.m00.real), float(H.m01.real), float(H.m02.real)],
         [float(H.m10.real), float(H.m11.real), float(H.m12.real)],
         [float(H.m20.real), float(H.m21.real), float(H.m22.real)]]
    # identity eigenvectors
    V = [[1.0, 0.0, 0.0],
         [0.0, 1.0, 0.0],
         [0.0, 0.0, 1.0]]
    def max_offdiag(M):
        i=j=0; m=0.0
        for r in range(3):
            for c in range(r+1,3):
                val=abs(M[r][c])
                if val>m: m=val; i=r; j=c
        return m,i,j
    it=0
    while True:
        m,i,j = max_offdiag(M)
        if m<tol or it>=max_iter: break
        it+=1
        # compute rotation
        if M[i][i]==M[j][j]:
            theta = math.pi/4
        else:
            tau = (M[j][j]-M[i][i])/(2*M[i][j])
            t = math.copysign(1.0, tau)/(abs(tau)+math.sqrt(1+tau*tau))
            theta = math.atan(t)
        c = math.cos(theta); s = math.sin(theta)
        # rotate M
        aii, ajj, aij = M[i][i], M[j][j], M[i][j]
        M[i][i] = c*c*aii - 2*s*c*aij + s*s*ajj
        M[j][j] = s*s*aii + 2*s*c*aij + c*c*ajj
        M[i][j] = M[j][i] = 0.0
        for k in range(3):
            if k!=i and k!=j:
                aik, ajk = M[i][k], M[j][k]
                M[i][k] = M[k][i] = c*aik - s*ajk
                M[j][k] = M[k][j] = s*aik + c*ajk
        # rotate V
        for k in range(3):
            vik, vjk = V[k][i], V[k][j]
            V[k][i] = c*vik - s*vjk
            V[k][j] = s*vik + c*vjk
    # eigenvalues on diag of M; eigenvectors are columns of V
    eigvals = [M[0][0], M[1][1], M[2][2]]
    eigvecs = [(V[0][0], V[1][0], V[2][0]),
               (V[0][1], V[1][1], V[2][1]),
               (V[0][2], V[1][2], V[2][2])]
    # normalize vectors
    def norm3(v):
        return math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]) or 1.0
    eigvecs = [tuple(x/ norm3(v) for x in v) for v in eigvecs]
    return eigvals, eigvecs
