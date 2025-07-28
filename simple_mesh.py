import trimesh
import os

def generate_simple_mesh(stl_path, msh_path=None):
    """
    Convert STL to mesh file (PLY format) with minimal processing
    """
    try:
        # Load STL
        mesh = trimesh.load(stl_path)
        
        # Simple validation
        if not mesh.is_watertight:
            print("⚠️ Warning: Mesh is not watertight - may cause issues")
        
        # Set default output path if not provided
        if msh_path is None:
            msh_path = os.path.splitext(stl_path)[0] + ".ply"
        
        # Export to PLY format (simple mesh format)
        mesh.export(msh_path)
        
        print(f"✅ Simple mesh saved to {msh_path}")
        return msh_path
        
    except Exception as e:
        print(f"❌ Simple mesh generation failed: {str(e)}")
        return None

# Example usage:
if __name__ == "__main__":
    generate_simple_mesh("input.stl", "output.ply")