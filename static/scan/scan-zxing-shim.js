/*
 * Pearnly · scan-zxing-shim.js · 把 ZXing 包成 BarcodeDetector 的形状
 *
 * 上层(scan-camera.js)只写一套解码代码:`new Detector({formats}).detect(canvas)`。
 * Detector 要么是浏览器原生 BarcodeDetector(安卓 Chrome 有),要么是这里造的同形状类
 * (iOS Safari 全系 + 桌面 Firefox/Safari 都没有原生的)。两条路的差异全压在这个文件里,
 * 上层不出现任何 `if (原生)` 分支 —— 分支一多,兜底那条路就永远没人测。
 *
 * 与原生的一处刻意差异:detect() 只吃 canvas,不吃 <video>。取景框裁剪在 scan-camera.js
 * 统一做完再喂进来(原生那条路同样只喂裁剪后的 canvas),两条路解的是同一块像素。
 */
(function (root) {
    'use strict';

    // 零售条码格式 → ZXing 枚举。故意不含 qr_code/data_matrix/aztec/pdf417:
    // 商品条码里没有二维码,多开一种格式就是每帧多跑一遍解码器白耗 CPU(手机上掉帧)。
    var FORMAT_NAMES = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf'];

    function formatMap(ZXing) {
        return {
            ean_13: ZXing.BarcodeFormat.EAN_13,
            ean_8: ZXing.BarcodeFormat.EAN_8,
            upc_a: ZXing.BarcodeFormat.UPC_A,
            upc_e: ZXing.BarcodeFormat.UPC_E,
            code_128: ZXing.BarcodeFormat.CODE_128,
            code_39: ZXing.BarcodeFormat.CODE_39,
            itf: ZXing.BarcodeFormat.ITF,
        };
    }

    // 「这一帧没读出码」的判定。走 instanceof + getKind() 两条,不看 err.name:
    // dist/zxing.js 是 minify 过的,类名会被改写,err.name 拿到的是混淆后的名字
    // (Odoo 原版比的就是 err.name,因为它 serve 的是未压缩源码 —— 照抄会把「没扫到」
    // 当成硬错误弹给店员,每秒弹好几次)。
    function isNoRead(ZXing, err) {
        if (!err) return false;
        if (ZXing.NotFoundException && err instanceof ZXing.NotFoundException) return true;
        if (ZXing.ChecksumException && err instanceof ZXing.ChecksumException) return true;
        var kind = typeof err.getKind === 'function' ? err.getKind() : '';
        return kind === 'NotFoundException' || kind === 'ChecksumException';
    }

    /**
     * @param {object} ZXing window.ZXing(dist/zxing.js 加载后的 UMD 全局)
     * @returns {function} BarcodeDetector 形状的构造函数
     */
    function build(ZXing) {
        var MAP = formatMap(ZXing);
        var REVERSE = Object.keys(MAP).map(function (name) {
            return [name, MAP[name]];
        });

        function ZXingBarcodeDetector(opts) {
            var wanted = (opts && opts.formats) || FORMAT_NAMES;
            var enums = [];
            for (var i = 0; i < wanted.length; i++) {
                if (MAP[wanted[i]] !== undefined) enums.push(MAP[wanted[i]]);
            }
            var hints = new Map();
            hints.set(ZXing.DecodeHintType.POSSIBLE_FORMATS, enums.length ? enums : [MAP.ean_13]);
            // TRY_HARDER 顺带打开 90° 旋转扫描(zxing-js/library#291)——横躺在货架上的
            // 条码、店员斜着凑过来的条码,不开这个就是「明明对准了却读不出」。
            hints.set(ZXing.DecodeHintType.TRY_HARDER, true);
            this.reader = new ZXing.MultiFormatReader();
            this.reader.setHints(hints);
        }

        ZXingBarcodeDetector.getSupportedFormats = function () {
            return Promise.resolve(FORMAT_NAMES.slice());
        };

        function formatNameOf(value) {
            for (var i = 0; i < REVERSE.length; i++) {
                if (REVERSE[i][1] === value) return REVERSE[i][0];
            }
            return 'unknown';
        }

        // 返回值形状对齐 Shape Detection API 的 DetectedBarcode:
        // {rawValue, format, boundingBox, cornerPoints}。上层只读前两个,后两个给足以免
        // 将来要画框时又得改这层。
        ZXingBarcodeDetector.prototype.detect = function (canvas) {
            var source = new ZXing.HTMLCanvasElementLuminanceSource(canvas);
            var bitmap = new ZXing.BinaryBitmap(new ZXing.HybridBinarizer(source));
            var result;
            try {
                result = this.reader.decodeWithState(bitmap);
            } catch (e) {
                // 没扫到 = NotFoundException / 校验位不对 = ChecksumException,都是常态不是错误
                // (每秒好几帧都这样)。其它异常(解码器内部炸了)如实往上抛,让上层走 onError。
                if (isNoRead(ZXing, e)) return Promise.resolve([]);
                return Promise.reject(e);
            }
            var pts = result.getResultPoints() || [];
            var a = pts[0] || { x: 0, y: 0 };
            var b = pts[1] || a;
            return Promise.resolve([
                {
                    rawValue: result.getText(),
                    format: formatNameOf(result.getBarcodeFormat()),
                    boundingBox: {
                        x: a.x,
                        y: a.y,
                        width: Math.max(1, Math.abs(b.x - a.x)),
                        height: Math.max(1, Math.abs(b.y - a.y)),
                    },
                    cornerPoints: pts,
                },
            ]);
        };

        return ZXingBarcodeDetector;
    }

    var api = { build: build, FORMAT_NAMES: FORMAT_NAMES };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanZXing = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
