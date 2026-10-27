import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { Project, SiteMapNode } from "@/types";
import { projectsApi } from "@/lib/api";
import toast from "react-hot-toast";

interface ProjectStore {
  projects: Project[];
  selectedProject: Project | null;
  siteMap: SiteMapNode[];
  isLoading: boolean;
  isCreating: boolean;
  isDeleting: boolean;

  fetchProjects: () => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  createProject: (data: { name: string; url: string; description?: string; headed?: boolean }) => Promise<Project | null>;
  deleteProject: (id: string) => Promise<boolean>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
  setSelectedProject: (project: Project | null) => void;
  fetchSiteMap: (projectId: string) => Promise<void>;
  runTests: (projectId: string, headed?: boolean) => Promise<string | null>;
}

export const useProjectStore = create<ProjectStore>()(
  devtools(
    (set, get) => ({
      projects: [],
      selectedProject: null,
      siteMap: [],
      isLoading: false,
      isCreating: false,
      isDeleting: false,

      fetchProjects: async () => {
        set({ isLoading: true });
        try {
          const res = await projectsApi.list();
          const rawItems = res.data?.items ?? res.data?.data ?? (Array.isArray(res.data) ? res.data : []);
          const projects: Project[] = rawItems.map((p: any) => ({
            id: p.id,
            name: p.name,
            url: p.url,
            status: p.status,
            description: p.description,
            testCount: p.testCount ?? 0,
            createdAt: p.created_at ?? p.createdAt ?? new Date().toISOString(),
            updatedAt: p.updated_at ?? p.updatedAt ?? new Date().toISOString(),
            pageCount: p.site_map?.pages_found ?? 0,
            siteMap: p.site_map,
          }));
          set({ projects, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },

      fetchProject: async (id: string) => {
        set({ isLoading: true });
        try {
          const res = await projectsApi.get(id);
          const p = res.data?.data ?? res.data;
          const project: Project = {
            id: p.id,
            name: p.name,
            url: p.url,
            status: p.status,
            description: p.description,
            testCount: p.testCount ?? 0,
            createdAt: p.created_at ?? p.createdAt ?? new Date().toISOString(),
            updatedAt: p.updated_at ?? p.updatedAt ?? new Date().toISOString(),
            pageCount: p.site_map?.pages_found ?? 0,
            siteMap: p.site_map,
          };
          set({ selectedProject: project, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },

      createProject: async (data) => {
        set({ isCreating: true });
        try {
          const res = await projectsApi.create(data);
          const p = res.data?.data ?? res.data;
          const project: Project = {
            id: p.id,
            name: p.name,
            url: p.url,
            status: p.status,
            description: p.description,
            testCount: 0,
            createdAt: p.created_at ?? p.createdAt ?? new Date().toISOString(),
            updatedAt: p.updated_at ?? p.updatedAt ?? new Date().toISOString(),
            pageCount: 0,
          };
          set((state) => ({
            projects: [project, ...state.projects],
            isCreating: false,
          }));
          toast.success("Project created successfully!");
          return project;
        } catch {
          set({ isCreating: false });
          return null;
        }
      },

      deleteProject: async (id: string) => {
        set({ isDeleting: true });
        try {
          await projectsApi.delete(id);
          set((state) => ({
            projects: state.projects.filter((p) => p.id !== id),
            isDeleting: false,
            selectedProject:
              state.selectedProject?.id === id ? null : state.selectedProject,
          }));
          toast.success("Project deleted.");
          return true;
        } catch {
          set({ isDeleting: false });
          return false;
        }
      },

      updateProject: async (id: string, data) => {
        try {
          const res = await projectsApi.update(id, data);
          const updated: Project = res.data?.data ?? res.data;
          set((state) => ({
            projects: state.projects.map((p) => (p.id === id ? updated : p)),
            selectedProject:
              state.selectedProject?.id === id ? updated : state.selectedProject,
          }));
        } catch {
          // error handled by interceptor
        }
      },

      setSelectedProject: (project) => set({ selectedProject: project }),

      fetchSiteMap: async (projectId: string) => {
        try {
          const res = await projectsApi.getSiteMap(projectId);
          const siteMap: SiteMapNode[] = res.data?.data ?? res.data ?? [];
          set({ siteMap });
        } catch {
          set({ siteMap: [] });
        }
      },

      runTests: async (projectId: string, headed?: boolean) => {
        try {
          const res = await projectsApi.runTests(projectId, headed);
          const runId: string = res.data?.data?.run_id ?? res.data?.run_id;
          toast.success("Test run started!");
          // update project status
          set((state) => ({
            projects: state.projects.map((p) =>
              p.id === projectId ? { ...p, status: "running" } : p
            ),
          }));
          return runId;
        } catch {
          return null;
        }
      },
    }),
    { name: "project-store" }
  )
);
