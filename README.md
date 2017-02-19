# VertAnimToTex 0.8
Maya tool to export vertex animation as textures and use them in vertex shaders.

# Install:

 * 1.Download and unzip the folder.
 * 2.Put it under Documents/Maya/Scripts/
 * 3.Open Autodesk Maya, in the script editor,switch to python label,input and excute
 
```python
import VertAnimToTex
VertAnimToTex.main()
```
# Manual:

![tool_window](https://cloud.githubusercontent.com/assets/5509512/23100104/89769834-f62c-11e6-97b0-79a7f5f2a186.PNG)
 
 * 1.After the window popout, select the mesh that with vertex animation. Input the animation start and end frame, 
   index texture size, set output path and texture name.
 * 2.Click export and wait for the data texture export process.
 * 3.Export the model. (Do not change frame)

![unity_index_import](https://cloud.githubusercontent.com/assets/5509512/23100103/8974257c-f62c-11e6-9754-9c6fc24af0e9.PNG)
![unity_data_import](https://cloud.githubusercontent.com/assets/5509512/23100102/896f8026-f62c-11e6-81e3-15d21fdcd66f.PNG)

* 4.In Unity, set the imported index and data texture as above.
* 5.Use the shader file [VertAnim.shader](https://github.com/ZGeng/VertAnimToTex/blob/master/VertAnim.shader) in the folder for the material. Put the index and data texture in the right slot.
* ** There are 3 preprocessor options in the shader file, to determine whether to use index data stored in the vertex color, 
    whether to use normal movement data and tangent movement data.

Featers in the upcoming version: Option about nomarl and tangent data output. Unity import tools. etc.

