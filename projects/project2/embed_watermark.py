import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.util import random_noise
class DCTWatermark:
    def __init__(self, strength=0.1, block_size=8, seed=42):
        self.strength = strength
        self.block_size = block_size
        self.seed = seed
        np.random.seed(seed)
    def _get_dct_blocks(self, img):
        h, w = img.shape
        blocks = []
        for y in range(0, h, self.block_size):
            for x in range(0, w, self.block_size):
                block = img[y:y+self.block_size, x:x+self.block_size]
                if block.shape == (self.block_size, self.block_size):
                    blocks.append((y, x, block))
        return blocks
    def embed(self, host_img, watermark):
        yuv = cv2.cvtColor(host_img, cv2.COLOR_BGR2YUV)
        Y = yuv[:, :, 0].astype(np.float32)
        wm_resized = cv2.resize(watermark, (Y.shape[1]//self.block_size, Y.shape[0]//self.block_size))
        wm_binary = (wm_resized > 128).astype(np.float32) * 2 - 1  # 转换为[-1, 1]
        blocks = self._get_dct_blocks(Y)
        watermarked_Y = Y.copy()
        for idx, (y, x, block) in enumerate(blocks):
            dct_block = cv2.dct(block)
            pos_x, pos_y = 3, 4
            if idx < wm_binary.size:
                dct_block[pos_y, pos_x] += self.strength * wm_binary.flat[idx]
            watermarked_block = cv2.idct(dct_block)
            watermarked_Y[y:y+self.block_size, x:x+self.block_size] = watermarked_block
        yuv[:, :, 0] = np.clip(watermarked_Y, 0, 255)
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    def extract(self, watermarked_img, watermark_shape):
        yuv = cv2.cvtColor(watermarked_img, cv2.COLOR_BGR2YUV)
        Y = yuv[:, :, 0].astype(np.float32)
        extracted = np.zeros(watermark_shape, dtype=np.float32).flatten()
        blocks = self._get_dct_blocks(Y)
        for idx, (y, x, block) in enumerate(blocks):
            if idx >= extracted.size:
                break
            dct_block = cv2.dct(block)
            pos_x, pos_y = 3, 4
            extracted[idx] = dct_block[pos_y, pos_x]
        extracted = extracted.reshape(watermark_shape)
        return (extracted > extracted.mean()).astype(np.uint8) * 255
from skimage.metrics import structural_similarity as ssim
def compare_images(img1, img2):
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    if len(img1.shape) == 3 and img1.shape[2] == 3:  # 如果是BGR三通道
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = img1 if len(img1.shape) == 2 else cv2.cvtColor(img1, cv2.COLOR_RGBA2GRAY)
    if len(img2.shape) == 3 and img2.shape[2] == 3:
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        gray2 = img2 if len(img2.shape) == 2 else cv2.cvtColor(img2, cv2.COLOR_RGBA2GRAY)
    mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
    psnr = 20 * np.log10(255.0 / np.sqrt(mse)) if mse > 0 else float('inf')
    ssim_val = ssim(
        gray1, gray2,
        data_range=255 if gray1.max() > 1 else 1,
        win_size=3
    )
    return psnr, ssim_val
def apply_attacks(img):
    attacked = {}
    attacked['flipped'] = cv2.flip(img, 1)
    M = np.float32([[1, 0, 20], [0, 1, 20]])
    attacked['translated'] = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
    h, w = img.shape[:2]
    cropped = img[h//8:h-h//8, w//8:w-w//8]
    attacked['cropped'] = cv2.resize(cropped, (w, h))
    attacked['contrast'] = np.clip(img * 1.5, 0, 255).astype(np.uint8)
    attacked['noisy'] = (random_noise(img, mode='gaussian', var=0.01) * 255).astype(np.uint8)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 30]
    _, encimg = cv2.imencode('.jpg', img, encode_param)
    attacked['jpeg'] = cv2.imdecode(encimg, 1)
    M = cv2.getRotationMatrix2D((img.shape[1]//2, img.shape[0]//2), 5, 1)
    attacked['rotated'] = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
    return attacked
def main():
    host = cv2.imread(r'C:\Users\Thinkpad\Desktop\projects\project2\host_image.jpg')
    watermark = cv2.imread(r'C:\Users\Thinkpad\Desktop\projects\project2\watermark.png', cv2.IMREAD_GRAYSCALE)
    watermarker = DCTWatermark(strength=0.2)
    watermarked_img = watermarker.embed(host, watermark)
    cv2.imwrite('watermarked.jpg', watermarked_img)
    extracted_wm = watermarker.extract(watermarked_img, watermark.shape)
    cv2.imwrite('extracted_original.png', extracted_wm)
    attacked_imgs = apply_attacks(watermarked_img)
    results = []
    for attack_name, attacked_img in attacked_imgs.items():
        extracted_attacked = watermarker.extract(attacked_img, watermark.shape)
        cv2.imwrite(f'attacked_{attack_name}.jpg', attacked_img)
        cv2.imwrite(f'extracted_{attack_name}.png', extracted_attacked)
        psnr, ssim = compare_images(extracted_wm, extracted_attacked)
        results.append((attack_name, psnr, ssim))
    print("\n鲁棒性测试结果:")
    print("-" * 40)
    print(f"{'攻击类型':<15} | {'PSNR (dB)':<10} | {'SSIM':<6}")
    print("-" * 40)
    for name, psnr, ssim in results:
        print(f"{name:<15} | {psnr:<10.2f} | {ssim:<6.4f}")
    print("-" * 40)
if __name__ == "__main__":
    main()