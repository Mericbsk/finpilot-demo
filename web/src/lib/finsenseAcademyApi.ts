import { apiJson } from "@/lib/api";

export type AcademyLocale = "tr" | "en" | "de";
export type AcademyLevel = "beginner" | "intermediate" | "advanced";

export interface FinSenseClaim {
  id: string;
  text: string;
  type: "conceptual" | "numeric" | "regulatory";
  source_ids: string[];
}

export interface FinSenseQuizQuestion {
  id: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  claim_ids: string[];
}

export interface FinSenseLesson {
  concept_id: string;
  locale: AcademyLocale;
  version: number;
  status: string;
  level: AcademyLevel;
  jurisdiction: string[];
  title: string;
  learning_objectives: string[];
  body_md: string;
  claims: FinSenseClaim[];
  quiz: FinSenseQuizQuestion[];
}

export interface FinSenseSource {
  id: string;
  title: string;
  publisher: string;
  url: string;
  section?: string;
  published: string;
  accessed: string;
  authority: string;
  jurisdiction?: string[];
}

export interface FinSenseCatalogEntry {
  lesson: FinSenseLesson;
  manifest_entry: {
    concept_id: string;
    locale: AcademyLocale;
    version: number;
    sha256: string;
    content_hash: string;
  };
  sources: FinSenseSource[];
}

export interface FinSenseAcademyCatalog {
  catalog_schema_version: string;
  locale: AcademyLocale;
  manifest_sha256: string;
  manifest: {
    release_id: string;
    manifest_schema_version: string;
    content_schema_version: string;
    policy_version: string;
    release_gate: {
      decision: "PASS";
      publisher: "central-release-gate";
    };
  };
  lessons: FinSenseCatalogEntry[];
}

export async function getAcademyCatalog(
  locale: AcademyLocale,
): Promise<FinSenseAcademyCatalog> {
  return apiJson<FinSenseAcademyCatalog>(
    `/api/v1/academy/catalog?locale=${encodeURIComponent(locale)}`,
  );
}