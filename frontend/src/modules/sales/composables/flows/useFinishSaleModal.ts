import { ref, computed, type Ref } from "vue";

import { PaymentSaleCreate } from "../../schemas/paymentSale.schema";

const finishModalIsOpen = ref(false);
const payments = ref<PaymentSaleCreate[]>([]);

export function useFinishSaleModal(saleTotal?: Ref<number>) {
    const totalPago = computed(() =>
        payments.value.reduce((sum, p) => sum + p.valor, 0)
    );

    const troco = computed(() => {
        const total = saleTotal?.value ?? 0;
        return Math.max(0, totalPago.value - total);
    });

    const restante = computed(() => {
        const total = saleTotal?.value ?? 0;
        return Math.max(0, total - totalPago.value);
    });

    const canFinish = computed(() =>
        payments.value.length > 0 && totalPago.value >= (saleTotal?.value ?? 0)
    );

    function addPayment(payment: PaymentSaleCreate) {
        payments.value.push(payment);
    }

    function removePayment(index: number) {
        payments.value.splice(index, 1);
    }

    function resetPayments() {
        payments.value = [];
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
        addPayment,
        removePayment,
        resetPayments,
        totalPago,
        troco,
        restante,
        canFinish,
    }
}