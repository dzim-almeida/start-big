import type { Meta, StoryObj } from '@storybook/vue3';
import BaseTab from './BaseTab.vue';

const meta: Meta<typeof BaseTab> = {
  title: 'Components/BaseTab',
  component: BaseTab,
  argTypes: {
    modelValue: {
      control: 'text',
    },
    tabs: {
      control: 'object',
    },
  },
};

export default meta;
type Story = StoryObj<typeof BaseTab>;

export const Default: Story = {
  args: {
    modelValue: 'tab1',
    tabs: [
      { id: 'tab1', label: 'Aba 1' },
      { id: 'tab2', label: 'Aba 2' },
    ],
  },
};

export const ThreeTabs: Story = {
  args: {
    modelValue: 'produtos',
    tabs: [
      { id: 'produtos', label: 'Produtos' },
      { id: 'servicos', label: 'Serviços' },
      { id: 'outros', label: 'Outros' },
    ],
  },
};

export const SecondTabActive: Story = {
  args: {
    modelValue: 'tab2',
    tabs: [
      { id: 'tab1', label: 'Primeiro' },
      { id: 'tab2', label: 'Segundo' },
      { id: 'tab3', label: 'Terceiro' },
    ],
  },
};

export const LoginRegisterTabs: Story = {
  args: {
    modelValue: 'login',
    tabs: [
      { id: 'login', label: 'Login' },
      { id: 'cadastro', label: 'Cadastro' },
    ],
  },
};

export const ManyTabs: Story = {
  args: {
    modelValue: 'dashboard',
    tabs: [
      { id: 'dashboard', label: 'Dashboard' },
      { id: 'vendas', label: 'Vendas' },
      { id: 'estoque', label: 'Estoque' },
      { id: 'relatorios', label: 'Relatórios' },
      { id: 'configuracoes', label: 'Configurações' },
    ],
  },
};