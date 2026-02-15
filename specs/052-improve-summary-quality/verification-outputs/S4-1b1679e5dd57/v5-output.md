```markdown
# Three.jsでデッサン人形風3Dモデルを作る手順

## 要約
Three.jsを使って漫画家が使うデッサン人形風の3Dモデルを作成し、マウス操作で関節を回転させる実装手順とコード例を紹介します。

## タグ
Three.js, 3Dモデリング, デッサン人形, ボーンアニメーション, WebGL

## 内容
### 技術スタック
| コンポーネント | 役割 |
|----------------|------|
| Three.js | 3Dレンダリング |
| SkinnedMesh | ボーンアニメーション |
| OrbitControls | 視点操作 |
| GUI (dat.GUI) | スライダー制御 |

### モデル作成
- **ジオメトリ**：円柱・球体を組み合わせて人体比率に合わせる。  
- **マテリアル**：`ToonMaterial` でセルシェーディング風に。  
- **木製質感**：テクスチャを薄茶色・濃茶色に設定。

### ボーンシステム設定
1. 肩・肘・膝・足首などに `Bone` を配置。  
2. `SkinnedMesh` でメッシュとボーンを連動。  
3. ボーン階層を自然に構築し、回転制御を可能に。

### UI実装
- **OrbitControls**：マウスドラッグで視点回転、ホイールでズーム。  
- **dat.GUI**：各関節の角度をスライダーで調整。  
- **ボタン**：ポーズリセット、ランダムポーズを実装。

### コード例（基本構造）
```javascript
import * as THREE from 'three';

// シーン設定
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight);
const renderer = new THREE.WebGLRenderer();

// ボーン構造作成
const bones = [];
const shoulderBone = new THREE.Bone();
const elbowBone = new THREE.Bone();
// ... 他の関節

// SkinnedMesh作成
const geometry = new THREE.CylinderGeometry(0.5, 0.5, 2);
const material = new THREE.MeshToonMaterial({ color: 0xffdbac });
const mesh = new THREE.SkinnedMesh(geometry, material);

// ポーズ変更関数
function changePose(jointName, rotation) {
    const bone = bones.find(b => b.name === jointName);
    if (bone) {
        bone.rotation.set(rotation.x, rotation.y, rotation.z);
    }
}
```  
```javascript
// Three.jsシーン、カメラ、レンダラーの初期化
// SkinnedMeshとボーンの作成
// OrbitControlsとdat.GUIの設定
```

### 高度な実装
- **IKシステム**：手足の先端位置から逆算でポーズ計算。  
- **プリセットポーズ**：JSONで保存・読み込み。  
- **アニメーション**：ポーズ間の補間でスムーズな動き。

### コード例（デッサン人形風モデル）
```javascript
// 頭：球体
const head = new THREE.SphereGeometry(0.6);

// 胴体：円柱
const torso = new THREE.CylinderGeometry(0.8, 1.0, 2.5);

// 手足：細い円柱
const arm = new THREE.CylinderGeometry(0.2, 0.2, 1.5);

// 関節：小さな球体
const joint = new THREE.SphereGeometry(0.3);
```  
```javascript
// 円柱・球体で構成されたデッサン人形のジオメトリ作成
// 木製テクスチャの適用
```

### 完成例と操作
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```  
```javascript
// 完成した3Dモデルのレンダリング
// マウスで関節をクリック＆ドラッグしてポーズ変更
// GUIで角度調整、リセット・ランダムポーズボタン
```

### まとめ
- Three.jsとSkinnedMeshで簡単にデッサン人形風3Dモデルを作成。  
- マウス操作とGUIで直感的にポーズを変更できる。  
- 必要に応じてIKやアニメーションを追加してさらにリアルに。

```