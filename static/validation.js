
// Validaciones frontend en JavaScript
class FrontendValidator {
    
    static validateEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(email);
    }
    
    static validatePhone(phone) {
        if (!phone) return false;
        const cleanPhone = phone.replace(/[^\d]/g, '');
        return cleanPhone.length >= 7 && cleanPhone.length <= 15;
    }
    
    static validatePassword(password) {
        if (!password) return { valid: false, error: "La contraseña es requerida" };
        if (password.length < 6) return { valid: false, error: "Mínimo 6 caracteres" };
        if (password.length > 128) return { valid: false, error: "Máximo 128 caracteres" };
        return { valid: true, error: "" };
    }
    
    static validateBalance(balance) {
        try {
            const balanceFloat = parseFloat(balance);
            if (balanceFloat < 0) return { valid: false, error: "El saldo no puede ser negativo" };
            if (balanceFloat > 999999.99) return { valid: false, error: "Saldo demasiado alto" };
            return { valid: true, error: "" };
        } catch (e) {
            return { valid: false, error: "Formato de saldo inválido" };
        }
    }
    
    static validatePrice(price, minPrice = 0.01, maxPrice = 1000.00) {
        try {
            const priceFloat = parseFloat(price);
            if (priceFloat < minPrice) return { valid: false, error: `Precio mínimo: $${minPrice}` };
            if (priceFloat > maxPrice) return { valid: false, error: `Precio máximo: $${maxPrice}` };
            return { valid: true, error: "" };
        } catch (e) {
            return { valid: false, error: "Formato de precio inválido" };
        }
    }
    
    static validateRegistrationForm(formData) {
        const errors = [];
        
        // Validar nombre
        if (!formData.nombre || formData.nombre.trim().length < 2) {
            errors.push("El nombre debe tener al menos 2 caracteres");
        }
        
        // Validar apellido
        if (!formData.apellido || formData.apellido.trim().length < 2) {
            errors.push("El apellido debe tener al menos 2 caracteres");
        }
        
        // Validar email
        if (!this.validateEmail(formData.email)) {
            errors.push("Formato de email inválido");
        }
        
        // Validar teléfono
        if (!this.validatePhone(formData.telefono)) {
            errors.push("Formato de teléfono inválido");
        }
        
        // Validar contraseña
        const passwordValidation = this.validatePassword(formData.password);
        if (!passwordValidation.valid) {
            errors.push(passwordValidation.error);
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    static validateRechargeForm(formData, gameType) {
        const errors = [];
        
        // Validar opción seleccionada
        if (!formData.option_value) {
            errors.push("Debes seleccionar una opción");
        }
        
        // Validar precio
        const priceValidation = this.validatePrice(formData.real_price);
        if (!priceValidation.valid) {
            errors.push(priceValidation.error);
        }
        
        // Validaciones específicas por juego
        if (gameType === 'block_striker') {
            if (!formData.player_id || formData.player_id.trim().length === 0) {
                errors.push("ID del jugador es requerido para Block Striker");
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    static showValidationErrors(errors, containerId = 'validation-errors') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (errors.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }
        
        const errorList = errors.map(error => `<li>${error}</li>`).join('');
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Errores de validación:</strong>
                <ul>${errorList}</ul>
            </div>
        `;
        container.style.display = 'block';
    }
    
    static formatCurrency(amount) {
        try {
            return `$${parseFloat(amount).toFixed(2)}`;
        } catch (e) {
            return '$0.00';
        }
    }
    
    static generateTransactionId(userId, prefix = 'TX') {
        const timestamp = Date.now();
        const random = Math.floor(Math.random() * 9000) + 1000;
        const userSuffix = userId.slice(-3);
        return `${prefix}${userSuffix}${timestamp.toString().slice(-5)}${random}`;
    }
    
    static cleanInput(text, maxLength = 255) {
        if (!text) return '';
        
        // Limpiar caracteres especiales
        let cleaned = text.toString().trim().replace(/[<>"']/g, '');
        
        // Truncar si es necesario
        if (cleaned.length > maxLength) {
            cleaned = cleaned.substring(0, maxLength);
        }
        
        return cleaned;
    }
    
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Funciones de utilidad global
function formatDateTime(timestamp = null) {
    const date = timestamp ? new Date(timestamp) : new Date();
    return date.toLocaleString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function calculateDiscount(originalPrice, discountPercent) {
    if (discountPercent <= 0) return originalPrice;
    
    const discountAmount = originalPrice * (discountPercent / 100);
    const finalPrice = originalPrice - discountAmount;
    return Math.round(finalPrice * 100) / 100;
}

function showMessage(text, type, containerId = 'message') {
    const messageDiv = document.getElementById(containerId);
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.textContent = '';
                messageDiv.className = 'message';
            }, 5000);
        }
    }
}

// Exportar para uso global
window.FrontendValidator = FrontendValidator;
window.formatDateTime = formatDateTime;
window.calculateDiscount = calculateDiscount;
window.showMessage = showMessage;
