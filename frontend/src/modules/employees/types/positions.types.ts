/**
 * @fileoverview Types for cargo (position) management
 * @description Matches backend schemas for cargos and UI helpers
 */

import type { Component } from 'vue';

export interface CargoBase {
  nome: string;
  permissoes: Record<string, boolean>;
}

export interface CargoCreate extends CargoBase {}

export interface CargoRead extends CargoBase {
  id: number;
  empresa_id: number;
}

export interface CargoUpdate {
  nome?: string;
  permissoes?: Record<string, boolean>;
}

export interface PositionFormData {
  nome: string;
  permissoes: Record<string, boolean>;
}

export interface PermissionMatrixItem {
  id: string;
  label: string;
  description: string;
  icon: Component;
  viewKey: string;
  manageKey: string;
  deleteKey: string;
}

export interface PositionCardTheme {
  accent: string;
  iconBg: string;
  ring: string;
  glow: string;
}

export type AccessLevelId =
  | 'administrator'
  | 'manager'
  | 'operational'
  | 'restricted';

export interface AccessLevelDefinition {
  id: AccessLevelId;
  label: string;
  description: string;
  badge: string;
  gradient: string;
  minRatio: number;
  filterColor: string;
}
