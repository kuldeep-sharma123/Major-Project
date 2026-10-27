"use client";

import { useCallback } from "react";
import { useProjectStore } from "@/store/project-store";

export function useProjects() {
  const {
    projects,
    selectedProject,
    siteMap,
    isLoading,
    isCreating,
    isDeleting,
    fetchProjects,
    fetchProject,
    createProject,
    deleteProject,
    updateProject,
    setSelectedProject,
    fetchSiteMap,
    runTests,
  } = useProjectStore();

  const handleCreate = useCallback(
    async (data: { name: string; url: string; description?: string; headed?: boolean }) => {
      return createProject(data);
    },
    [createProject]
  );

  const handleDelete = useCallback(
    async (id: string) => {
      return deleteProject(id);
    },
    [deleteProject]
  );

  const handleRunTests = useCallback(
    async (projectId: string, headed?: boolean) => {
      return runTests(projectId, headed);
    },
    [runTests]
  );

  return {
    projects,
    selectedProject,
    siteMap,
    isLoading,
    loading: isLoading,
    isCreating,
    isDeleting,
    fetchProjects,
    fetchProject,
    createProject: handleCreate,
    deleteProject: handleDelete,
    updateProject,
    setSelectedProject,
    fetchSiteMap,
    runTests: handleRunTests,
  };
}
