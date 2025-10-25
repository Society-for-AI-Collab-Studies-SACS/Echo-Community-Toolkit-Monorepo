import math
from echo_soulcode.operators import spectral_jacobi, H_ECHO

def test_spectral_jacobi_reconstruct_pure():
    evals, evecs = spectral_jacobi(H_ECHO)
    # reconstruct H ≈ V diag(λ) V^T using pure python
    def matmul3(A,B):
        return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    V = [[evecs[0][0], evecs[1][0], evecs[2][0]],
         [evecs[0][1], evecs[1][1], evecs[2][1]],
         [evecs[0][2], evecs[1][2], evecs[2][2]]]
    L = [[evals[0],0.0,0.0],[0.0,evals[1],0.0],[0.0,0.0,evals[2]]]
    VT = [[V[j][i] for j in range(3)] for i in range(3)]
    Hrec = matmul3(matmul3(V, L), VT)
    H = [[float(H_ECHO.m00.real), float(H_ECHO.m01.real), float(H_ECHO.m02.real)],
         [float(H_ECHO.m10.real), float(H_ECHO.m11.real), float(H_ECHO.m12.real)],
         [float(H_ECHO.m20.real), float(H_ECHO.m21.real), float(H_ECHO.m22.real)]]
    for i in range(3):
        for j in range(3):
            assert abs(H[i][j]-Hrec[i][j]) < 1e-5
