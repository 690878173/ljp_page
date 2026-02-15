const CryptoJS = require('crypto-js');

function p() {
        var e = ["17073bbnsPV", "3863270olZElm", "SEA".split("").reverse().join(""), "edDtr", "15XxrXAy", "JZIHne1185023".split("").reverse().join(""), "kvvQaW609638".split("").reverse().join(""), "qZNtGh5".split("").reverse().join(""), "752826NycBGl", "tilps".split("").reverse().join(""), "oaQjU".split("").reverse().join(""), "3056HZARTJ", "OhAtzd482145".split("").reverse().join(""), "3|4|1|0|2", "gnirtsbus".split("").reverse().join(""), "tpyrcne".split("").reverse().join(""), "random", "46esaB".split("").reverse().join(""), "Hex", "mode", "NoPadding", "pad", "WordArray", "gnirts".split("").reverse().join(""), "gnirtSot".split("").reverse().join(""), "esrap".split("").reverse().join(""), "key", "CFB", "htgnel".split("").reverse().join(""), "WB0nMZHXlxNndORe", "DLDZT", "8ftU".split("").reverse().join(""), "stringify", "cne".split("").reverse().join(""), "ERtKP", "decrypt", "496484aCEWpj", "lib", "ciphertext"];
        return e
    }
function l(e, a) {
        var t = p();
        return t[e -= 0]
    }
jia = function(e) {
            function a(e, a, t, n, i) {
                return l(e - -186, n)
            }
            var t = function(e, a) {
                return e + a
            }
              , n = function(e, a) {
                return e ^ a
            }
              , i = ["3","4","1","0","2"]
              , o = 0;
            for (; ; ) {
                switch (i[o++]) {
                case "0":
                    console.log('执行0')
                    var s = CryptoJS.AES.encrypt(c, d, {
                        iv: r,
                        mode: CryptoJS.mode.CFB,
                        padding: CryptoJS.pad.NoPadding
                    }).ciphertext.toString(CryptoJS.enc.Hex);
                    continue;
                case "1":
                    console.log('执行1')
                    var c = CryptoJS.enc.Utf8.parse(typeof e === a(-152, 0, 0, -163) ? e : JSON.stringify(e));
                    continue;
                case "2":
                    console.log('执行2')
                    return t(t(s.substring(0, 16), CryptoJS.enc.Hex.stringify(r)), s.substring(16));
                case "3":
                    console.log('执行3')
                    var r = CryptoJS.lib.WordArray.random(n(941931, 941947));
                    continue;
                case "4":
                    console.log('执行4')
                    var d = CryptoJS.enc.Utf8.parse('WB0nMZHXlxNndORe');
                    continue
                }
                console.log('执行5')
                break
            }
        }

jie = function(e) {
            var a = function(e, a) {
                return e ^ a
            }
              , t = function(e, a) {
                return e ^ a
            }
              , n = e.length
              , i = "".split("").reverse().join("")
              , o = "".split("").reverse().join("")
              , s = "".split("").reverse().join("");
            n < a(989400, 989416) ? (i = e.substring(t(266432, 266432), n - 32),
            s = e.substring(n - 32)) : (i = e.substring(0, 16),
            o = e.substring(a(685351, 685335)),
            s = e.substring(16, 48));
            var c = CryptoJS.enc.Hex.parse(i + o)
              , r = CryptoJS.enc.Base64.stringify(c)
              , d = CryptoJS.enc.Hex.parse(s)
              , l = CryptoJS.enc.Utf8.parse('WB0nMZHXlxNndORe')
              , u = CryptoJS.AES.decrypt(r, l, {
                iv: d,
                mode: CryptoJS.mode.CFB,
                padding: CryptoJS.pad.NoPadding
            });
            return JSON.parse(u.toString(CryptoJS.enc.Utf8))
        }


data = "b99222770b76ef0d68655648524e51424b46647371663341234d8a2c3cb512cf7c7ac50e1aeca2ce1406e5e25440c6a5d6f18917a12ede9ef341170876670b334a462f6588d8145c00178a4b9ae48f2e6d03fcceb2a61b03d125701da2779061811493d42df8fb7a6b4d05387a9a26d2f593336709d2abb9b6457fd036f06ed6560ceeae0ce2079d95fc25ed85c4e975a5c9d6726069798b4d1f9cc85e4a85a221cb60d579e1ce2c2110a65c5ab48b9aa02dbe6d341ddfe9461b3f38a1e727bbdcfc2002458c5c613351ece3aef3162ba64d380ca578867f0f03164929e4ea0b378b9bd316dcccc4795eee7a51fe0c692fa9d78ed6b7cf1ae8d268b566dfce91de79c44c84191ee4fa4bc702cbcb523b538f275a69757f39c96d072537a9f777e6063b63551dc7f888ee911a84b5a9d6fca9760f58e8810de6ef16e333c998589700fb21eb60cc692ed886d04771d1a3069c623c9ba164b4bff705b5c322999e1bd8360b1597328e5e71674397896e3ac63e78cfc70dddfa66e063217490c1a3fc7f6806754a0f177aa15833bff5f18a64ae713cda2c3dc9f961a5c7ffdac790c6dabe1b3a3f4671b3742199de05a297634be7ad98b2a564d2ec32046c4644cc4b316203b678307df270a8f7128fee37c61f7067e93616ce46fc90442e9f2e3d2bd0c5a3172003adaa2a1df044178fa4cce78300061c9059f480a2a185b9f8c2036bddd09567458a5db11accbbe3ed562398393846f40db4d66161fd6eecdfb766f4157cce5d1ad116c9991e5f016e114c9a95bb6b53ffc25fe4cc4dbc0d65883bf0bb53b62599e16bdfac6ff7d69692533b676b690921e00a65830c9f7c6328fef4b10e94fbfaf3daa051a4a1018cc6918cb1ff53ef8d8c3aea7a5e1dd6964e87454b7b52afce4e5f3bc7ffe9d8910cfde432e797c3548b8d1c01a73f044cbe0c6607871ca285839432f13fa2a0d019ea02d5128d4189062ba867d79a66dd2e2dd6582b78ac58dd1a5d376d62f52ea8adb2a0c4c0bfe7091348eebd4a716f6923d534236a741e8f18ca23fe3369d765d0704a5e6d4f3d41efa514b372806730da52bf59e143f31c666d4f2ea37641a0a8b5984827058776174ec98301b960a43abe5069db11ea08830ae23763295066c4c6dce43820a1eee72f33be0d14028ad9e187c3ab795b2c68a22ba13ce73f68f67cc70f656ca07153e04c092d69d9c6797c640c6aa3f43754a2aa705fe9209d403de17d0d3fca0681f9414a8a366e643a3e75b206d8dbcd1e1c938a8b324be7b54822439ded6052c9bedf845b7f6cce3cb61b70671fb9a2f5f1ebbaa36b1718c5f7d6c74790d55c136cbf5d2143d35ed608fad6276e68a3bfdb2b84ddf15779ad0d44f0463e325c6b40aca075"

rt = jie(data)


data2 = {
    id: 170690, site: 50, token: null, timestamp: 1760039211
}
console.log(data2)
j = jia(data2)
data = "83226ea7301fb4ed416a7141734d305a6964777957377071a009b5962929dd00d183f4f52d1e3e9ba3bcf32a8aec271e58b5f55099e4af7f0d58d0422b640c8c724dce9347a1ecc67d61a4af399ea9a26ad2a1138d2154bb6f31fe064900d943d31a64750916f41c6bed27772a026d37dd6e433472a82a81e5088a64f69f0f30f0d99730b3a68da1b19322d281e7f22245907e7f7d41397fe2265c15325e774ebdc298c46b63f41d869b07834ee0a94529d2e89c97660b59195f68fd2393fe491fff8e1755080fd7141091c4dd4c500391be882b53e0e06f2d4dfd5e869313658a819badfbd923a8620a7c4491cfffda5cfb197874452e3c6a0db9ea1e03fd578f994e4cb657cacb014f4fd1796fd14c25444c1aa2f1f7dd67f56d30880f8355f5dff47b781311c2810a4d30d40286be68f3d98ea207466d40a62d913cf0d7f9917270affb7a38ccc57490300c39e65661bd6198a126e0bf8c3f562ff635126a9126e32db3814da62b44e5ffb6ef8ca151d56d738d54ec5efa0ed50efc8d970ba67c672fe3f6bc028c9daa80eea777cb67459e055904f1475d1c9ed8c10a16e468d10f80eb0d8d9bcd68820721c6d0b7d20e2283e00f522fe9328b7854097c36f18cbe252e2851e36fe373db5b1034f83e12eeba36b627fa6eeab724eba1c89979353b1aed6823c2bceb28118953ec7349087880f0a4287317a3f52256cebac9a2ffdf607b8f65cf7f2970b4e31167dd7dbf6570e7d5f798e74432992d87340a1a5c9d719612d30ef20d56b978b8db38a14aeb7f9674204f92b520f11322eb985ec896d9b0800cd5ded50efc18b16ffd8e08ff8bac832a69895140bd4578135d4a7f75e4ee18e7b9315c715fdae1d533f6ceca57d9cf1c7be26d1422eb42ff14c4154b2ed721abe642e9874cb40c70197c8616134ef319a77c7c52c982dc29c6649e7e68bcd5ce0b78d35fd7768fc485bea85fdc4f99c8fb3698b218fa04d9ce8563cbfa94a0775a1cb8fda0b19da8987f475e0bdc501652b683f64269a5012520d963b7751aff0fb1576cc8d733d785aecff318f614e15fe19a83ed7e3494b23b3b1ab15a5dffb781465aaf44a7114c6e899464e500cca83140df25ec7f4a94b7dd4208bfc22be5b8249285440410b0aa8c9db29775849abf7eca614e1e133b87527f5e2d3df71337a0221d5b655cfefeda3579fd82405a2064949ed8d858d015597351aea562dd6c591cc23ac6c28dcfba1434cdb2dc6fbb2c24336d7ae704352c3765db528d59fbc9c62d7183b54b0420fc9aea1a99015e6c7967bc6fb7adfb5e8e9ca1db841902336500eb3ed4ab1546113f0cd6765b3fc4e8247fea0b61200bd7f14a1b380d2ec66bceda6ad3934dd61008bc927dcb70963abbdd"

console.log(j)
q = jie(data)
console.log(q.vod_down_url[0].list[0].url)
console.log(rt.vod_down_url[0].list[0].url)

