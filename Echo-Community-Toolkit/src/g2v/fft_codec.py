import numpy as np

def fft_encode(img):
    return np.fft.fftshift(np.fft.fft2(np.asarray(img, float)))

def ifft_decode(F):
    return np.real(np.fft.ifft2(np.fft.ifftshift(np.asarray(F))))

