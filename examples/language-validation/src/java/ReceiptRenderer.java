package examples.languagevalidation;

public final class ReceiptRenderer {
    private ReceiptRenderer() {
    }

    public static String renderReceipt(long totalCents) {
        return "Receipt total: " + totalCents;
    }
}
