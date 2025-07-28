import trimesh
import os
import numpy as np
from scipy.spatial import KDTree


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
    

def compute_distance_field(stl_path, mesh_path):
    """
    Computes min distance between STL vertices and mesh nodes.
    Returns:
        - distance_field (numpy array): Min distance for each mesh node
        - distance_mesh (trimesh.Trimesh): Mesh with distance field as vertex color
    """
    # Load both files
    stl = trimesh.load(stl_path)
    mesh = trimesh.load(mesh_path)
    
    # Build KDTree for fast nearest-neighbor search
    stl_kdtree = KDTree(stl.vertices)
    
    # Compute min distance for each mesh node
    distances, _ = stl_kdtree.query(mesh.vertices)
    distance_field = np.array(distances)
    
    # Create colored mesh for visualization
    distance_mesh = mesh.copy()
    
    # Normalize distances for better color mapping
    normalized_dist = (distances - distances.min()) / (distances.max() - distances.min())
    distance_mesh.visual.vertex_colors = trimesh.visual.interpolate(
        normalized_dist, color_map='viridis')
    
    return distance_field, distance_mesh    

# Example usage:
if __name__ == "__main__":
    generate_simple_mesh("input.stl", "output.ply")