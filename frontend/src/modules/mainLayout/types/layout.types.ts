import type { Component } from "vue";

//Opcoes de menu existente
export type sidebarTitles =
    | 'MENU PRINCIPAL'
    | 'EMPRESA'

export type sidebarLabelOptions = 
    | 'Início'
    | 'Vendas'
    | 'Serviços'
    | 'Clientes'
    | 'Produtos'
    | 'Estoque'
    | 'Catálogo'
    | 'Dados da Empresa'
    | 'Funcionários'

export type requiredPermission =
    | 'view_dashboard'
    | 'view_sales'
    | 'view_services'
    | 'view_customers'
    | 'view_products'
    | 'view_storage'
    | 'view_catalog'
    | 'view_enterprise'
    | 'view_employees'
    
export interface SidebarOption {
    id: string;
    icon: Component;
    label: sidebarLabelOptions;
    requiredPermission: requiredPermission;
}

export interface SidebarSection {
    title: sidebarTitles;
    options: SidebarOption[];
}