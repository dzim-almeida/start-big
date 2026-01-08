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
    
export interface sidebarOption {
    id: string;
    icon: Component;
    label: sidebarLabelOptions;
}

export interface sidebarSection {
    title: sidebarTitles;
    options: sidebarOption[];
}