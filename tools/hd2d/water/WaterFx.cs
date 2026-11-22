// 萌叮 HD-2D 水面接入：场景加载后调用 WaterFx.Apply(root)，把材质名为 water / sea / pool 的材质换成 MengDing/HD2DWater 并按预设设参数。
// 放到 unity/Assets/HD2D_Forest3D/（或场景脚本所在目录）；water_normal.png 放 Resources/HD2DWater/（导入设置：Texture Type = Normal map，Wrap = Repeat，Filter = Point 保持像素感，或 Bilinear 更柔）。
using UnityEngine;

public static class WaterFx
{
    static Shader shader;
    static Texture2D normal;

    public static void Apply(GameObject root)
    {
        if (shader == null) shader = Shader.Find("MengDing/HD2DWater");
        if (shader == null) { Debug.LogWarning("[WaterFx] 找不到 MengDing/HD2DWater（是否进了 Always Included Shaders）"); return; }
        if (normal == null) normal = Resources.Load<Texture2D>("HD2DWater/water_normal");
        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
        {
            var mats = r.sharedMaterials;
            bool changed = false;
            for (int i = 0; i < mats.Length; i++)
            {
                var m = mats[i]; if (m == null) continue;
                string n = m.name.Replace(" (Instance)", "").ToLowerInvariant();
                string kind = n.StartsWith("sea") ? "sea" : n.StartsWith("pool") ? "pool" : n.StartsWith("water") ? "river" : null;
                if (kind == null || m.shader == shader) continue;
                var w = new Material(shader) { name = m.name + "_hd2dwater" };
                if (normal != null) w.SetTexture("_NormalTex", normal);
                Preset(w, kind);
                mats[i] = w; changed = true;
            }
            if (changed)
            {
                r.sharedMaterials = mats;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
        }
    }

    static void Preset(Material w, string kind)
    {
        switch (kind)
        {
            case "river":   // 松果林小溪：清澈偏绿，顺坡往下流，池塘几乎不动（顶点色 B 控制）
                w.SetColor("_ShallowColor", new Color(0.42f, 0.86f, 0.80f, 0.50f));
                w.SetColor("_DeepColor", new Color(0.10f, 0.42f, 0.52f, 0.90f));
                w.SetFloat("_DeepDist", 1.2f); w.SetFloat("_FoamWidth", 0.22f);
                w.SetFloat("_UseFlow", 1); w.SetFloat("_FlowSpeed", 0.8f); w.SetFloat("_NormalTiling", 0.45f);
                w.SetFloat("_WaveAmp", 0); w.SetFloat("_TideAmp", 0);
                break;
            case "sea":     // 珊瑚港：浅水碧绿透底，远处深蓝，起浪 + 潮汐
                w.SetColor("_ShallowColor", new Color(0.36f, 0.88f, 0.84f, 0.45f));
                w.SetColor("_DeepColor", new Color(0.05f, 0.36f, 0.60f, 0.95f));
                w.SetFloat("_DeepDist", 7f); w.SetFloat("_FoamWidth", 0.7f);
                w.SetFloat("_UseFlow", 0); w.SetFloat("_NormalTiling", 0.22f);
                w.SetFloat("_WaveAmp", 0.09f); w.SetFloat("_WaveLen", 8f); w.SetFloat("_WaveSpeed", 1.0f);
                w.SetFloat("_TideAmp", 0.12f); w.SetFloat("_TidePeriod", 28f); w.SetFloat("_BeachSlope", 0.12f);
                break;
            default:        // 喷泉、潮池：静水，轻微波光
                w.SetColor("_ShallowColor", new Color(0.50f, 0.88f, 0.90f, 0.55f));
                w.SetColor("_DeepColor", new Color(0.30f, 0.70f, 0.80f, 0.75f));
                w.SetFloat("_UseFlow", 0); w.SetFloat("_WaveAmp", 0); w.SetFloat("_TideAmp", 0);
                w.SetFloat("_FoamWidth", 0); w.SetFloat("_NormalTiling", 0.6f); w.SetFloat("_DeepDist", 1f);
                break;
        }
    }
}
