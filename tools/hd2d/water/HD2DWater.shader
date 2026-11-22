// 萌叮 HD-2D 水面（内置管线，移动端）：河流流动 + 海面起伏波浪 + 潮汐涨落 + 岸边浪花 + 菲涅尔天空反射 + 太阳高光
// 不用深度贴图（省一遍深度绘制）：离岸距离、流向都由场景生成器写在顶点色里：
//   R,G = 流向（Blender 的 x,y，*.5+.5）  B = 流速系数（河 1，池塘 .15；海 1 表示要起浪）  A = 离岸距离（.5 + 米/16）
// 预设见 WaterFx.cs：材质名 water → 河，sea → 海，pool → 静水（喷泉、潮池）。
Shader "MengDing/HD2DWater"
{
    Properties
    {
        _ShallowColor ("浅水色", Color) = (0.36, 0.86, 0.84, 0.55)
        _DeepColor ("深水色", Color) = (0.06, 0.38, 0.58, 0.93)
        _SkyColor ("天空反射色", Color) = (0.78, 0.9, 1, 1)
        _FoamColor ("浪花色", Color) = (1, 1, 1, 1)
        _NormalTex ("法线贴图（可平铺）", 2D) = "bump" {}
        _NormalTiling ("法线每米重复", Float) = 0.28
        _NormalStrength ("法线强度", Range(0, 2)) = 0.85
        _DeepDist ("多远算深水（米）", Float) = 5
        _FoamWidth ("岸边浪花宽（米）", Float) = 0.6
        _UseFlow ("按顶点流向流动（河）", Float) = 1
        _FlowSpeed ("流速（米/秒）", Float) = 0.7
        _FlowSign ("流向符号 x,y（导入轴向不对时改 -1）", Vector) = (1, 1, 0, 0)
        _FlowSwap ("流向 xy 互换（0/1）", Float) = 0
        _WaveAmp ("浪高（米）", Float) = 0
        _WaveLen ("波长（米）", Float) = 7
        _WaveSpeed ("浪速", Float) = 1.1
        _TideAmp ("潮汐高度（米）", Float) = 0
        _TidePeriod ("潮汐周期（秒）", Float) = 26
        _BeachSlope ("沙滩坡度（算浪花随潮进退）", Float) = 0.12
        _Spec ("太阳高光", Float) = 1.3
        _PixelSnap ("像素对齐（每米像素，0 关）", Float) = 32
    }
    SubShader
    {
        Tags { "Queue" = "Transparent-10" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Pass
        {
            Tags { "LightMode" = "ForwardBase" }
            ZWrite Off
            Blend SrcAlpha OneMinusSrcAlpha
            Cull Back
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma target 3.0
            #include "UnityCG.cginc"
            #include "Lighting.cginc"

            fixed4 _ShallowColor, _DeepColor, _SkyColor, _FoamColor;
            sampler2D _NormalTex;
            float _NormalTiling, _NormalStrength, _DeepDist, _FoamWidth, _UseFlow, _FlowSpeed, _FlowSwap;
            float4 _FlowSign;
            float _WaveAmp, _WaveLen, _WaveSpeed, _TideAmp, _TidePeriod, _BeachSlope, _Spec, _PixelSnap;

            struct appdata { float4 vertex : POSITION; float4 color : COLOR; };
            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 wpos : TEXCOORD0;
                float3 wnrm : TEXCOORD1;
                float4 col : TEXCOORD2;     // rg 流向, b 流速, a 离岸
                float crest : TEXCOORD3;    // 浪尖（白沫）
                UNITY_FOG_COORDS(4)
            };

            // 三道方向不同的 Gerstner 浪，返回位移，顺便算法线
            float3 gerstner(float2 p, float t, out float3 n, out float crest)
            {
                float3 d = 0; float3 nn = float3(0, 1, 0); crest = 0;
                float2 dirs[3] = { float2(-0.86, 0.5), float2(-0.5, -0.86), float2(-0.98, -0.2) };
                float lens[3] = { 1.0, 0.62, 0.37 };
                float amps[3] = { 1.0, 0.55, 0.3 };
                [unroll] for (int i = 0; i < 3; i++)
                {
                    float L = _WaveLen * lens[i]; float k = 6.2832 / L; float A = _WaveAmp * amps[i];
                    float c = sqrt(9.8 / k) * _WaveSpeed;
                    float f = k * (dot(dirs[i], p) - c * t);
                    float Q = 0.45;
                    d.xz += Q * A * dirs[i] * cos(f);
                    d.y += A * sin(f);
                    nn.xz -= dirs[i] * k * A * cos(f);
                    nn.y -= Q * k * A * sin(f);
                    crest += amps[i] * saturate(sin(f));
                }
                n = normalize(nn); crest /= 1.85;
                return d;
            }

            v2f vert(appdata v)
            {
                v2f o;
                float3 w = mul(unity_ObjectToWorld, v.vertex).xyz;
                float3 n = float3(0, 1, 0); float crest = 0;
                float shore = (v.color.a - 0.5) * 16;              // 米，海里为正
                if (_WaveAmp > 0)
                {
                    // 越靠岸浪越小（浅水），岸上那一圈不动，免得穿出地面
                    float fade = saturate((shore + 1) / 6);
                    float3 n2; float c2;
                    float3 d = gerstner(w.xz, _Time.y, n2, c2);
                    w += d * fade; n = normalize(lerp(float3(0, 1, 0), n2, fade)); crest = c2 * fade;
                }
                w.y += _TideAmp * sin(_Time.y * 6.2832 / max(_TidePeriod, 1));
                o.pos = mul(UNITY_MATRIX_VP, float4(w, 1));
                o.wpos = w; o.wnrm = n; o.col = v.color; o.crest = crest;
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            float3 sampleN(float2 uv) { return UnpackNormal(tex2D(_NormalTex, uv)); }

            fixed4 frag(v2f i) : SV_Target
            {
                float2 p = i.wpos.xz;
                if (_PixelSnap > 0) p = floor(p * _PixelSnap) / _PixelSnap;   // 和场景像素贴图一样 1 米 32 格
                float t = _Time.y;
                float3 tn;
                if (_UseFlow > 0.5)
                {
                    // 流动贴图（flow map）：两相交替，避免拉伸
                    float2 fd = i.col.rg * 2 - 1;
                    if (_FlowSwap > 0.5) fd = fd.yx;
                    fd *= _FlowSign.xy;
                    float spd = _FlowSpeed * i.col.b;
                    float ph0 = frac(t * 0.35), ph1 = frac(t * 0.35 + 0.5);
                    float2 uv = p * _NormalTiling;
                    float3 a = sampleN(uv - fd * spd * ph0 / 0.35 * _NormalTiling);
                    float3 b = sampleN(uv - fd * spd * ph1 / 0.35 * _NormalTiling + 0.37);
                    float wgt = abs(1 - 2 * ph0);
                    tn = normalize(lerp(b, a, wgt) + sampleN(uv * 2.3 + t * 0.02) * 0.35);
                }
                else
                {
                    float2 uv = p * _NormalTiling;
                    tn = normalize(sampleN(uv + float2(0.03, 0.017) * t) + sampleN(uv * 1.7 + float2(-0.021, 0.028) * t));
                }
                tn.xy *= _NormalStrength;
                float3 N = normalize(float3(i.wnrm.x + tn.x, i.wnrm.y, i.wnrm.z + tn.y));
                float3 V = normalize(_WorldSpaceCameraPos - i.wpos);
                float3 L = normalize(_WorldSpaceLightPos0.xyz);

                float shore = (i.col.a - 0.5) * 16;                                   // 米
                float tide = _TideAmp * sin(t * 6.2832 / max(_TidePeriod, 1));
                float d = shore + tide / max(_BeachSlope, 0.02);                      // 涨潮时水线往岸上推
                float depthT = saturate(d / _DeepDist);
                fixed4 col = lerp(_ShallowColor, _DeepColor, depthT);

                float fres = pow(1 - saturate(dot(N, V)), 4);
                col.rgb = lerp(col.rgb, _SkyColor.rgb, fres * 0.55);
                float3 H = normalize(L + V);
                col.rgb += _LightColor0.rgb * pow(saturate(dot(N, H)), 160) * _Spec;
                col.rgb *= 0.75 + 0.25 * saturate(dot(N, L));

                // 岸边浪花：一条随时间一层层推上岸的白边 + 浪尖碎沫
                float wave = frac(d / max(_FoamWidth * 3, 0.1) - t * 0.25);
                float edge = saturate(1 - d / _FoamWidth);
                float foam = edge * (0.55 + 0.45 * step(0.6, wave));
                float nz = tex2D(_NormalTex, p * 0.9 + t * 0.05).r;
                foam = saturate(foam - nz * 0.35) + saturate(i.crest - 0.72) * 2.2 * step(0.55, nz);
                if (_PixelSnap > 0) foam = step(0.5, foam) * 0.9;                   // 像素风：浪花是硬边
                col.rgb = lerp(col.rgb, _FoamColor.rgb, foam);
                col.a = saturate(col.a + foam * 0.6 + fres * 0.2);
                col.a *= saturate(d * 2 + 1);                                          // 水线处淡出，不出现硬切边
                UNITY_APPLY_FOG(i.fogCoord, col);
                return col;
            }
            ENDCG
        }
    }
    Fallback "Transparent/Diffuse"
}
