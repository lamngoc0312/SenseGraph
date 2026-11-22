/* SenseGraph Phase 16 — Modular Learning Library, Local Progress, & Educator Authoring
 *
 * Exposes `window.SenseGraphLibrary`:
 *  - ProgressStore: local-only browser storage (never syncs externally, zero PII)
 *  - LessonLibraryController: catalog filtering, search, difficulty, next-lesson recommendation
 *  - EducatorPackageTool: safe JSON lesson package export & import validated via backend
 */

(() => {
  "use strict";

  const STORAGE_KEY = "sensegraph_progress_v1";

  class ProgressStore {
    constructor() {
      this.data = this._load();
    }

    _defaultData() {
      return {
        currentLessonId: null,
        currentStep: "welcome",
        completedLessonIds: [],
        attempts: {},
      };
    }

    _load() {
      try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (!raw) return this._defaultData();
        const parsed = JSON.parse(raw);
        return {
          currentLessonId: parsed.currentLessonId || null,
          currentStep: parsed.currentStep || "welcome",
          completedLessonIds: Array.isArray(parsed.completedLessonIds)
            ? parsed.completedLessonIds
            : [],
          attempts:
            parsed.attempts && typeof parsed.attempts === "object"
              ? parsed.attempts
              : {},
        };
      } catch {
        return this._defaultData();
      }
    }

    _save() {
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
      } catch {
        // Storage disabled or full; operate gracefully in-memory
      }
    }

    setCurrent(lessonId, step) {
      this.data.currentLessonId = lessonId;
      if (step) this.data.currentStep = step;
      this._save();
    }

    recordAttempt(lessonId) {
      if (!lessonId) return;
      this.data.attempts[lessonId] = (this.data.attempts[lessonId] || 0) + 1;
      this._save();
    }

    markCompleted(lessonId) {
      if (!lessonId) return;
      if (!this.data.completedLessonIds.includes(lessonId)) {
        this.data.completedLessonIds.push(lessonId);
      }
      this._save();
    }

    isCompleted(lessonId) {
      return this.data.completedLessonIds.includes(lessonId);
    }

    getAttempts(lessonId) {
      return this.data.attempts[lessonId] || 0;
    }

    getSummary(totalLessons) {
      return {
        completedCount: this.data.completedLessonIds.length,
        totalLessons,
        currentLessonId: this.data.currentLessonId,
      };
    }

    clear() {
      this.data = this._defaultData();
      try {
        window.localStorage.removeItem(STORAGE_KEY);
      } catch {
        // Ignore storage errors
      }
    }
  }

  class LessonLibraryController {
    constructor(apiRequestFn) {
      this.apiRequest = apiRequestFn;
      this.lessons = [];
      this.selectedDomain = "";
      this.selectedDifficulty = "";
      this.searchQuery = "";
    }

    async loadAll() {
      this.lessons = await this.apiRequest("/api/lessons");
      return this.lessons;
    }

    async fetchLessonDetail(lessonId) {
      return this.apiRequest(`/api/lessons/${encodeURIComponent(lessonId)}`);
    }

    getFilteredLessons() {
      const q = (this.searchQuery || "").trim().toLowerCase();
      return this.lessons.filter((lesson) => {
        if (this.selectedDomain && lesson.domain !== this.selectedDomain) {
          return false;
        }
        if (this.selectedDifficulty && lesson.difficulty !== this.selectedDifficulty) {
          return false;
        }
        if (q) {
          const hay = [
            lesson.title,
            lesson.description,
            lesson.domain,
            ...(lesson.learning_objectives || []),
          ]
            .join(" ")
            .toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      });
    }

    getRecommendedNext(currentLessonId, completedIds = []) {
      if (!this.lessons.length) return null;
      const curIdx = this.lessons.findIndex((l) => l.lesson_id === currentLessonId);
      if (curIdx >= 0) {
        const curDomain = this.lessons[curIdx].domain;
        // Prefer next uncompleted lesson in the same domain first
        const sameDomainNext = this.lessons.find(
          (l, idx) =>
            idx > curIdx &&
            l.domain === curDomain &&
            !completedIds.includes(l.lesson_id)
        );
        if (sameDomainNext) return sameDomainNext;
      }
      // Otherwise next uncompleted lesson overall
      const anyUncompleted = this.lessons.find(
        (l) => l.lesson_id !== currentLessonId && !completedIds.includes(l.lesson_id)
      );
      if (anyUncompleted) return anyUncompleted;
      return this.lessons[(Math.max(curIdx, 0) + 1) % this.lessons.length];
    }
  }

  class EducatorPackageTool {
    constructor(apiRequestFn) {
      this.apiRequest = apiRequestFn;
    }

    buildPackage({ diagram, title, description, difficulty, objectivesText }) {
      const objectives = (objectivesText || "")
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      const slug = (title || diagram.title || "custom_lesson")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_|_$/g, "")
        .slice(0, 48);

      return {
        lesson: {
          lesson_id: `custom_${slug || "lesson"}`,
          title: (title || diagram.title).trim(),
          domain: diagram.domain,
          difficulty: difficulty || "beginner",
          description: (description || diagram.summary).trim(),
          learning_objectives:
            objectives.length > 0
              ? objectives
              : ["Explore verified diagram components and relationships."],
          prerequisites: [],
          diagram_id: diagram.id,
          estimated_duration: "5 min",
          lesson_steps: [
            {
              step_id: "explore",
              title: "Explore Components",
              instruction: "Inspect each component one by one.",
            },
            {
              step_id: "experiment",
              title: "Predict & Experiment",
              instruction: "Run the verified domain check.",
            },
          ],
          supported_actions: [],
          challenges: [],
          explanations: [diagram.summary],
          review_status: diagram.review_status,
          provenance: "Educator-authored validated lesson package",
        },
        diagram,
      };
    }

    async validatePackage(pkg) {
      return this.apiRequest("/api/lessons/validate-package", {
        method: "POST",
        body: JSON.stringify(pkg),
      });
    }

    downloadJson(pkg, filename) {
      const blob = new Blob([JSON.stringify(pkg, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || `${pkg.lesson.lesson_id}.sensegraph.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }
  }

  window.SenseGraphLibrary = {
    ProgressStore,
    LessonLibraryController,
    EducatorPackageTool,
  };
})();
