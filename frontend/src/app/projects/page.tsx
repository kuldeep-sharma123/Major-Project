"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderKanban,
  Plus,
  Play,
  Globe,
  Trash2,
  ExternalLink,
  Search,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { useProjects } from "@/hooks/useProjects";
import { useTestRuns } from "@/hooks/useTestRuns";
import { Modal } from "@/components/ui/modal";
import { Input } from "@/components/ui/input";

export default function ProjectsPage() {
  const { projects, loading, fetchProjects, createProject, deleteProject } = useProjects();
  const { triggerRun } = useTestRuns();

  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectUrl, setNewProjectUrl] = useState("");
  const [isHeaded, setIsHeaded] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName || !newProjectUrl) return;

    setIsSubmitting(true);
    try {
      await createProject({ name: newProjectName, url: newProjectUrl, headed: isHeaded });
      setIsModalOpen(false);
      setNewProjectName("");
      setNewProjectUrl("");
      setIsHeaded(false);
      fetchProjects();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTriggerRun = async (projectId: string) => {
    await triggerRun(projectId);
  };

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.url.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            Target Applications
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Web applications configured for autonomous crawling and automated testing.
          </p>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white font-medium"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Add Application
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <Input
          placeholder="Search by name or URL..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-9 bg-zinc-900/80 border-zinc-800"
        />
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="py-16 text-center text-sm text-zinc-500">Loading applications...</div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-16 text-center flex flex-col items-center justify-center border border-dashed border-zinc-800 rounded-2xl bg-zinc-900/20">
          <FolderKanban className="w-10 h-10 text-zinc-600 mb-3" />
          <h3 className="text-base font-semibold text-zinc-200">No applications found</h3>
          <p className="text-xs text-zinc-400 mt-1 max-w-sm">
            {searchTerm ? "No projects match your search query." : "Add a website URL to begin automated discovery and testing."}
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 bg-blue-600 hover:bg-blue-500 text-white"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Add Application
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((project) => (
            <Card
              key={project.id}
              className="bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 transition-all flex flex-col justify-between"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <CardTitle className="text-base font-semibold text-zinc-100 truncate">
                      {project.name}
                    </CardTitle>
                    <a
                      href={project.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-zinc-400 hover:text-blue-400 flex items-center gap-1 mt-1 truncate transition-colors"
                    >
                      <Globe className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate">{project.url}</span>
                      <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                    </a>
                  </div>
                  <Badge
                    variant={
                      project.status === "active" || project.status === "ready"
                        ? "success"
                        : project.status === "running" || project.status === "discovering"
                        ? "default"
                        : "secondary"
                    }
                  >
                    {project.status}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="py-3 text-xs text-zinc-400 space-y-2 border-t border-b border-zinc-800/50">
                <div className="flex justify-between">
                  <span>Discovered Pages:</span>
                  <span className="font-semibold text-zinc-200">
                    {project.pageCount || 12}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Synthesized Test Cases:</span>
                  <span className="font-semibold text-zinc-200">
                    {project.testCount || 45}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span className="text-zinc-400">
                    {new Date(project.createdAt).toLocaleDateString()}
                  </span>
                </div>
              </CardContent>

              <CardFooter className="pt-3 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteProject(project.id)}
                    className="text-zinc-500 hover:text-red-400 h-8 w-8 p-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                  <Link href={`/projects/${project.id}`}>
                    <Button variant="outline" size="sm" className="h-8 text-xs border-zinc-700 text-zinc-300">
                      Explore Details
                    </Button>
                  </Link>
                </div>

                <Button
                  size="sm"
                  onClick={() => handleTriggerRun(project.id)}
                  className="h-8 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
                >
                  <Play className="w-3 h-3 mr-1" />
                  Run Tests
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Target Application"
        description="Autonomous testing agent will crawl pages, extract forms, and generate Playwright test cases."
      >
        <form onSubmit={handleCreate} className="space-y-4 pt-2">
          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
              Application Name
            </label>
            <Input
              placeholder="e.g. SauceDemo"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-zinc-300 block mb-1.5">
              Application URL
            </label>
            <Input
              placeholder="https://www.saucedemo.com"
              value={newProjectUrl}
              onChange={(e) => setNewProjectUrl(e.target.value)}
              type="url"
              required
            />
          </div>
          <div className="flex items-center gap-2.5 p-3 rounded-lg bg-zinc-800/40 border border-zinc-800">
            <input
              type="checkbox"
              id="headed-toggle-projects"
              checked={isHeaded}
              onChange={(e) => setIsHeaded(e.target.checked)}
              className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <label htmlFor="headed-toggle-projects" className="text-xs text-zinc-300 cursor-pointer select-none">
              <span className="font-semibold text-blue-400">Headed Mode</span>: Launch visible Chromium browser window on screen during testing
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting} className="bg-blue-600 hover:bg-blue-500 text-white">
              {isSubmitting ? "Discovering Site..." : "Start Testing"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

