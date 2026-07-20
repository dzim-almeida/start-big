import { ref, computed, type Ref } from "vue";

import { PaymentSaleCreate } from "../../schemas/paymentSale.schema";

const finishModalIsOpen = ref(false);
const payments = ref<PaymentSaleCreate[]>([]);
// Juros (em centavos) embutido em cada pagamento, na mesma ordem de `payments`.
// Mantido em paralelo para calcular o acréscimo total sem poluir o payload.
const paymentsJuros = ref<number[]>([]);

export function useFinishSaleModal(saleTotal?: Ref<number>) {
    const totalPago = computed(() =>
        payments.value.reduce((sum, p) => sum + p.valor, 0)
    );

    // Acréscimo total = soma dos juros de todos os pagamentos.
    const acrescimo = computed(() =>
        paymentsJuros.value.reduce((sum, j) => sum + j, 0)
    );

    // Total a pagar já considerando o acréscimo de juros do checkout.
    const totalComAcrescimo = computed(() => (saleTotal?.value ?? 0) + acrescimo.value);

    const troco = computed(() =>
        Math.max(0, totalPago.value - totalComAcrescimo.value)
    );

    const restante = computed(() =>
        Math.max(0, totalComAcrescimo.value - totalPago.value)
    );

    const canFinish = computed(() =>
        payments.value.length > 0 && totalPago.value >= totalComAcrescimo.value
    );

    function addPayment(payment: PaymentSaleCreate, juros = 0) {
        payments.value.push(payment);
        paymentsJuros.value.push(juros);
    }

    function removePayment(index: number) {
        payments.value.splice(index, 1);
        paymentsJuros.value.splice(index, 1);
    }

    function resetPayments() {
        payments.value = [];
        paymentsJuros.value = [];
    }

    function openFinishModal() {
        finishModalIsOpen.value = true;
    }

    function closeFinishModal() {
        resetPayments();
        finishModalIsOpen.value = false;
    }

    return {
        finishModalIsOpen,
        openFinishModal,
        closeFinishModal,
        payments,
        paymentsJuros,
        addPayment,
        removePayment,
        resetPayments,
        totalPago,
        acrescimo,
        troco,
        restante,
        canFinish,
    }
}
