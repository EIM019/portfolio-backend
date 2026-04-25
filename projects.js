import { useEffect, useState } from "react";
import { fallbackProjects } from "./fallbackProjects";

export default function Projects() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetch("https://portfolio-backend-72pr.onrender.com/projects")
      .then(res => res.json())
      .then(data => setProjects(data.projects))
      .catch(() => {
        // fallback if API fails
        setProjects(fallbackProjects);
      });
  }, []);

  return (
    <div>
      {projects.map(p => (
        <div key={p.id}>
          <h2>{p.title}</h2>
          <p>{p.description}</p>
        </div>
      ))}
    </div>
  );
}