/**
 * Lecturer Dashboard - QR Code Management
 * Handles all QR code related functionality for the lecturer dashboard
 */

document.addEventListener('alpine:data', () => {
    Alpine.data('lecturerDashboard', () => ({
        // QR Code State
        activeSessions: [],
        generatedQRCode: null,
        selectedModule: '',
        duration: 15,
        isLoading: false,
        error: null,
        showQRModal: false,
        
        // Module Data
        modules: [],
        
        // Attendance Data
        attendanceStats: [],
        attendanceChart: null,
        
        // Initialize component
        async init() {
            try {
                // Load modules and active sessions in parallel
                await Promise.all([
                    this.loadModules(),
                    this.loadActiveSessions(),
                    this.loadAttendanceStats()
                ]);
                
                // Initialize charts after data is loaded
                this.$nextTick(() => {
                    this.initializeCharts();
                });
                
            } catch (error) {
                console.error('Error initializing dashboard:', error);
                this.showToast('Failed to initialize dashboard. Please refresh the page.', 'error');
            }
        },
        
        // Load modules for the current lecturer
        async loadModules() {
            try {
                this.isLoading = true;
                const response = await fetch('{% url "dashboard:api:lecturer:modules" %}');
                if (!response.ok) throw new Error('Failed to load modules');
                this.modules = await response.json();
            } catch (error) {
                console.error('Error loading modules:', error);
                this.showToast('Failed to load modules. Please try again.', 'error');
            } finally {
                this.isLoading = false;
            }
        },
        
        // Load active QR sessions
        async loadActiveSessions() {
            try {
                this.isLoading = true;
                const response = await fetch('{% url "dashboard:qr:active_sessions" %}');
                if (!response.ok) throw new Error('Failed to load active sessions');
                const data = await response.json();
                
                // Process sessions to add UI state
                this.activeSessions = data.sessions.map(session => ({
                    ...session,
                    created_at: new Date(session.created_at),
                    expires_at: new Date(session.expires_at),
                    is_expired: new Date(session.expires_at) < new Date(),
                    expires_soon: (new Date(session.expires_at) - new Date()) < (15 * 60 * 1000), // 15 minutes
                    time_remaining: Math.max(0, Math.floor((new Date(session.expires_at) - new Date()) / 1000))
                }));
                
                // Update time remaining every second for active sessions
                this.activeSessions.forEach(session => {
                    if (!session.is_expired && !session.intervalId) {
                        session.intervalId = setInterval(() => {
                            const timeRemaining = Math.max(0, Math.floor((new Date(session.expires_at) - new Date()) / 1000));
                            session.time_remaining = timeRemaining;
                            session.is_expired = timeRemaining <= 0;
                            session.expires_soon = timeRemaining < (15 * 60); // 15 minutes
                            
                            if (session.is_expired && session.intervalId) {
                                clearInterval(session.intervalId);
                            }
                        }, 1000);
                    }
                });
                
            } catch (error) {
                console.error('Error loading active sessions:', error);
                this.showToast('Failed to load active sessions. Please try again.', 'error');
            } finally {
                this.isLoading = false;
            }
        },
        
        // Generate new QR code
        async generateQRCode() {
            if (!this.selectedModule) {
                this.error = 'Please select a module';
                return;
            }

            try {
                this.isLoading = true;
                this.error = null;
                
                const response = await fetch('{% url "dashboard:qr:generate_qr" %}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        module_id: this.selectedModule,
                        duration: this.duration
                    })
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to generate QR code');
                }

                this.generatedQRCode = data.qr_code;
                this.showQRModal = true;
                
                // Reload active sessions
                await this.loadActiveSessions();
                
                // Show success message
                this.showToast('QR code generated successfully!', 'success');
                
            } catch (error) {
                console.error('Error generating QR code:', error);
                this.error = error.message || 'Failed to generate QR code. Please try again.';
                this.showToast(this.error, 'error');
            } finally {
                this.isLoading = false;
            }
        },
        
        // End a session
        async endSession(sessionId) {
            if (!sessionId) return;
            
            try {
                // Find the session and update UI state
                const session = this.activeSessions.find(s => s.id === sessionId);
                if (!session) return;
                
                session.is_ending = true;
                
                const response = await fetch(`/dashboard/lecturer/qr/deactivate/${sessionId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': '{{ csrf_token }}',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to end session');
                }
                
                // Remove the session from the list
                this.activeSessions = this.activeSessions.filter(s => s.id !== sessionId);
                
                // Show success message
                this.showToast('Session ended successfully', 'success');
                
            } catch (error) {
                console.error('Error ending session:', error);
                this.error = error.message || 'Failed to end session. Please try again.';
                this.showToast(this.error, 'error');
            } finally {
                const session = this.activeSessions.find(s => s.id === sessionId);
                if (session) session.is_ending = false;
            }
        },
        
        // Copy QR code URL to clipboard
        async copyQRUrl(url) {
            try {
                await navigator.clipboard.writeText(url);
                this.showToast('QR code URL copied to clipboard!', 'success');
            } catch (err) {
                console.error('Failed to copy URL: ', err);
                this.showToast('Failed to copy URL to clipboard', 'error');
            }
        },
        
        // Format time remaining in a human-readable format
        formatTimeRemaining(seconds) {
            if (seconds <= 0) return 'Expired';
            
            // Convert seconds to hours, minutes, seconds
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = seconds % 60;
            
            let result = [];
            if (hours > 0) result.push(`${hours}h`);
            if (minutes > 0 || hours > 0) result.push(`${minutes}m`);
            result.push(`${remainingSeconds}s`);
            
            return result.join(' ');
        },
        
        // Format date to relative time
        timeSince(date) {
            const seconds = Math.floor((new Date() - new Date(date)) / 1000);
            
            let interval = Math.floor(seconds / 31536000);
            if (interval > 1) return interval + ' years';
            if (interval === 1) return 'a year';
            
            interval = Math.floor(seconds / 2592000);
            if (interval > 1) return interval + ' months';
            if (interval === 1) return 'a month';
            
            interval = Math.floor(seconds / 86400);
            if (interval > 1) return interval + ' days';
            if (interval === 1) return 'a day';
            
            interval = Math.floor(seconds / 3600);
            if (interval > 1) return interval + ' hours';
            if (interval === 1) return 'an hour';
            
            interval = Math.floor(seconds / 60);
            if (interval > 1) return interval + ' minutes';
            if (interval === 1) return 'a minute';
            
            return Math.floor(seconds) + ' seconds';
        },
        
        // Show toast notification
        showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg text-white ${
                type === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 300);
            }, 3000);
        },
        
        // Initialize charts for attendance visualization
        initializeCharts() {
            // Implementation for attendance charts
            // This would be called after data is loaded
        },
        
        // Clean up intervals when component is destroyed
        destroy() {
            // Clear all intervals for active sessions
            this.activeSessions.forEach(session => {
                if (session.intervalId) {
                    clearInterval(session.intervalId);
                }
            });
        }
    }));
});
