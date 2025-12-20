// الدوال المساعدة
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
        return 'الآن';
    } else if (diffMin < 60) {
        return `منذ ${diffMin} دقيقة`;
    } else if (diffHour < 24) {
        return `منذ ${diffHour} ساعة`;
    } else if (diffDay < 7) {
        return `منذ ${diffDay} يوم`;
    } else {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('ar-EG', options);
    }
}

// تطبيق Vue الرئيسي
new Vue({
    el: '#app',
    data: {
        currentView: 'home',
        currentUser: null,
        profileUser: null,
        posts: [],
        userPosts: [],
        suggestedUsers: [],
        trends: [],
        trendingHashtags: [],
        searchQuery: '',
        searchResults: [],
        showNewPostModal: false,
        newPostContent: '',
        postImage: null,
        postVideo: null,
        quickPostContent: '',
        newCommentContent: {},
        newReplyContent: {},
        profileTab: 'posts',
        settings: {
            username: '',
            email: '',
            bio: '',
            private_account: false,
            show_activity_status: true,
            email_notifications: true,
            push_notifications: true,
            language: 'ar',
            theme: 'light'
        },
        showUserMenu: false,
        isLoading: true,
        error: null
    },
    
    computed: {
        isCurrentUserProfile() {
            return this.profileUser && this.currentUser && 
                   this.profileUser.id === this.currentUser.id;
        }
    },
    
    async created() {
        await this.initializeApp();
    },
    
    methods: {
        async initializeApp() {
            try {
                await this.fetchCurrentUser();
                await this.fetchPosts();
                await this.fetchSuggestedUsers();
                this.isLoading = false;
                document.querySelector('#app').classList.add('ready');
                document.querySelector('#loading').style.display = 'none';
            } catch (error) {
                console.error('Error initializing app:', error);
                this.error = 'فشل تحميل التطبيق';
                this.isLoading = false;
                
                // إذا لم يكن المستخدم مسجلاً، أعد توجيهه للصفحة الرئيسية
                if (error.response && error.response.status === 401) {
                    window.location.href = '/login/';
                }
            }
        },
        
        async fetchCurrentUser() {
            try {
                const response = await axios.get('/api/users/me/');
                this.currentUser = response.data;
                this.profileUser = { ...response.data };
                return this.currentUser;
            } catch (error) {
                console.error('Error fetching user:', error);
                throw error;
            }
        },
        
        async fetchPosts() {
            try {
                const response = await axios.get('/api/posts/');
                this.posts = response.data.results || response.data;
                this.posts.forEach(post => {
                    post.showComments = false;
                    Vue.set(this.newCommentContent, post.id, '');
                });
            } catch (error) {
                console.error('Error fetching posts:', error);
            }
        },
        
        async fetchSuggestedUsers() {
            try {
                const response = await axios.get('/api/users/?limit=5');
                this.suggestedUsers = response.data.results || response.data.slice(0, 5);
            } catch (error) {
                console.error('Error fetching suggested users:', error);
            }
        },
        
        async createPost() {
            try {
                const formData = new FormData();
                formData.append('content', this.newPostContent);
                formData.append('post_type', this.postImage ? 'image' : this.postVideo ? 'video' : 'text');
                
                if (this.postImage) {
                    // إذا كانت postImage هي Data URL، حولها إلى Blob
                    if (this.postImage.startsWith('data:')) {
                        const blob = this.dataURLtoBlob(this.postImage);
                        formData.append('image', blob, 'image.jpg');
                    }
                }
                
                const response = await axios.post('/api/posts/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });
                
                this.posts.unshift(response.data);
                this.newPostContent = '';
                this.postImage = null;
                this.postVideo = null;
                this.showNewPostModal = false;
            } catch (error) {
                console.error('Error creating post:', error);
                alert('حدث خطأ أثناء نشر التغريدة');
            }
        },
        
        dataURLtoBlob(dataURL) {
            const arr = dataURL.split(',');
            const mime = arr[0].match(/:(.*?);/)[1];
            const bstr = atob(arr[1]);
            let n = bstr.length;
            const u8arr = new Uint8Array(n);
            
            while(n--) {
                u8arr[n] = bstr.charCodeAt(n);
            }
            
            return new Blob([u8arr], { type: mime });
        },
        
        async createQuickPost() {
            try {
                const response = await axios.post('/api/posts/', {
                    content: this.quickPostContent,
                    post_type: 'text'
                });
                
                this.posts.unshift(response.data);
                this.quickPostContent = '';
            } catch (error) {
                console.error('Error creating quick post:', error);
                alert('حدث خطأ أثناء نشر التغريدة');
            }
        },
        
        async toggleLike(post) {
            try {
                const response = await axios.post(`/api/posts/${post.id}/like/`);
                
                if (response.data.status === 'liked') {
                    post.likes_count++;
                    post.liked = true;
                } else {
                    post.likes_count--;
                    post.liked = false;
                }
            } catch (error) {
                console.error('Error toggling like:', error);
            }
        },
        
        async fetchComments(post) {
            try {
                const response = await axios.get(`/api/posts/${post.id}/comments/`);
                post.comments = response.data;
                post.comments.forEach(comment => {
                    comment.showReply = false;
                    Vue.set(this.newReplyContent, comment.id, '');
                });
            } catch (error) {
                console.error('Error fetching comments:', error);
            }
        },
        
        toggleCommentSection(post) {
            post.showComments = !post.showComments;
            if (post.showComments && !post.comments) {
                this.fetchComments(post);
            }
        },
        
        async addComment(post) {
            if (!this.newCommentContent[post.id] || !this.newCommentContent[post.id].trim()) {
                return;
            }
            
            try {
                const response = await axios.post(`/api/posts/${post.id}/comment/`, {
                    content: this.newCommentContent[post.id]
                });
                
                if (!post.comments) {
                    post.comments = [];
                }
                post.comments.push(response.data);
                post.comments_count++;
                this.newCommentContent[post.id] = '';
            } catch (error) {
                console.error('Error adding comment:', error);
                alert('حدث خطأ أثناء إضافة التعليق');
            }
        },
        
        replyToComment(comment, post) {
            comment.showReply = !comment.showReply;
            Vue.set(this.newReplyContent, comment.id, '');
        },
        
        async addReply(comment, post) {
            if (!this.newReplyContent[comment.id] || !this.newReplyContent[comment.id].trim()) {
                return;
            }
            
            try {
                const response = await axios.post(`/api/comments/${comment.id}/reply/`, {
                    content: this.newReplyContent[comment.id],
                    parent: comment.id
                });
                
                if (!comment.replies) {
                    comment.replies = [];
                }
                comment.replies.push(response.data);
                comment.showReply = false;
                this.newReplyContent[comment.id] = '';
            } catch (error) {
                console.error('Error adding reply:', error);
                alert('حدث خطأ أثناء إضافة الرد');
            }
        },
        
        changeView(view) {
            this.currentView = view;
            this.showUserMenu = false;
        },
        
        addImage() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        this.postImage = e.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            };
            input.click();
        },
        
        addVideo() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'video/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        this.postVideo = e.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            };
            input.click();
        },
        
        addImageToQuickPost() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    // تحويل إلى Data URL للإظهار الفوري
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        // أضف الصورة إلى محتوى المنشور السريع
                        this.quickPostContent += ` [صورة] `;
                        // يمكنك حفظ الصورة في متغير منفصل هنا
                    };
                    reader.readAsDataURL(file);
                }
            };
            input.click();
        },
        
        addVideoToQuickPost() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'video/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.quickPostContent += ` [فيديو] `;
                }
            };
            input.click();
        },
        
        async search() {
            if (this.searchQuery.length < 2) {
                this.searchResults = [];
                return;
            }
            
            try {
                const response = await axios.get(`/api/users/search/?q=${this.searchQuery}`);
                this.searchResults = response.data;
            } catch (error) {
                console.error('Error searching:', error);
            }
        },
        
        async toggleFollow(user) {
            try {
                const response = await axios.post(`/api/users/${user.id}/follow/`);
                
                user.is_following = !user.is_following;
                
                if (response.data.status === 'followed') {
                    user.followers_count++;
                    this.currentUser.following_count++;
                } else {
                    user.followers_count--;
                    this.currentUser.following_count--;
                }
            } catch (error) {
                console.error('Error toggling follow:', error);
            }
        },
        
        viewUserProfile(user) {
            this.profileUser = user;
            this.currentView = 'profile';
            this.fetchUserPosts(user.id);
        },
        
        async fetchUserPosts(userId) {
            try {
                const response = await axios.get(`/api/users/${userId}/posts/`);
                this.userPosts = response.data;
            } catch (error) {
                console.error('Error fetching user posts:', error);
            }
        },
        
        async saveSettings() {
            try {
                const response = await axios.put(`/api/users/${this.currentUser.id}/settings/`, 
                    this.settings);
                
                this.currentUser = { ...this.currentUser, ...response.data };
                alert('تم حفظ الإعدادات بنجاح');
            } catch (error) {
                console.error('Error saving settings:', error);
                alert('حدث خطأ أثناء حفظ الإعدادات');
            }
        },
        
        handleProfileImageUpload(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.settings.profile_image = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        },
        
        handleCoverImageUpload(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.settings.cover_image = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        },
        
        toggleUserMenu() {
            this.showUserMenu = !this.showUserMenu;
        },
        
        async logout() {
            try {
                await axios.post('/api/logout/');
                window.location.href = '/login/';
            } catch (error) {
                console.error('Error logging out:', error);
            }
        }
    },
    
    template: `
    <div class="min-h-screen bg-gray-50" v-if="!isLoading && !error">
        <!-- Header/Navigation -->
        <nav class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <i class="fab fa-twitter text-blue-500 text-2xl ml-3"></i>
                        <div class="hidden md:block">
                            <div class="mr-10 flex items-baseline space-x-4 space-x-reverse">
                                <a href="#" @click.prevent="changeView('home')" 
                                   :class="{'active-nav': currentView === 'home'}" 
                                   class="px-3 py-2 rounded-md text-sm font-medium">
                                    <i class="fas fa-home ml-1"></i> الرئيسية
                                </a>
                                <a href="#" @click.prevent="changeView('explore')"
                                   :class="{'active-nav': currentView === 'explore'}"
                                   class="px-3 py-2 rounded-md text-sm font-medium">
                                    <i class="fas fa-hashtag ml-1"></i> استكشف
                                </a>
                                <a href="#" @click.prevent="changeView('profile')"
                                   :class="{'active-nav': currentView === 'profile'}"
                                   class="px-3 py-2 rounded-md text-sm font-medium">
                                    <i class="fas fa-user ml-1"></i> الملف الشخصي
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Search Bar -->
                    <div class="flex items-center">
                        <div class="relative">
                            <input type="text" 
                                   v-model="searchQuery"
                                   @input="search"
                                   placeholder="بحث عن أشخاص أو تغريدات..."
                                   class="bg-gray-100 rounded-full py-2 px-4 pr-10 w-64 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <i class="fas fa-search absolute right-3 top-3 text-gray-400"></i>
                        </div>
                        
                        <!-- User Menu -->
                        <div class="mr-3 relative" v-if="currentUser">
                            <button @click="toggleUserMenu" class="flex items-center">
                                <img :src="currentUser.profile_image || '/static/images/default-profile.png'" 
                                     class="h-8 w-8 rounded-full object-cover"
                                     :alt="currentUser.username">
                                <span class="mr-2 text-sm font-medium">@{{ currentUser.username }}</span>
                            </button>
                            
                            <!-- Dropdown Menu -->
                            <div v-if="showUserMenu" class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border">
                                <a href="#" @click.prevent="changeView('profile')" class="block px-4 py-2 text-sm hover:bg-gray-100">
                                    <i class="fas fa-user ml-2"></i> الملف الشخصي
                                </a>
                                <a href="#" @click.prevent="changeView('settings')" class="block px-4 py-2 text-sm hover:bg-gray-100">
                                    <i class="fas fa-cog ml-2"></i> الإعدادات
                                </a>
                                <hr class="my-1">
                                <a href="#" @click.prevent="logout" class="block px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
                                    <i class="fas fa-sign-out-alt ml-2"></i> تسجيل الخروج
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="px-4 py-6 sm:px-0">
                <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    <!-- Left Sidebar -->
                    <div class="lg:col-span-1">
                        <div class="bg-white rounded-lg shadow p-4 mb-6 sidebar">
                            <div class="text-center mb-6">
                                <img :src="currentUser.profile_image || '/static/images/default-profile.png'" 
                                     class="h-24 w-24 rounded-full mx-auto object-cover border-4 border-white shadow"
                                     :alt="currentUser.username">
                                <h3 class="mt-3 font-bold text-lg">@{{ currentUser.username }}</h3>
                                <p class="text-gray-600 text-sm">{{ currentUser.bio }}</p>
                                
                                <div class="flex justify-center mt-4 space-x-6">
                                    <div class="text-center">
                                        <p class="font-bold">{{ currentUser.following_count }}</p>
                                        <p class="text-gray-600 text-sm">متابَعون</p>
                                    </div>
                                    <div class="text-center">
                                        <p class="font-bold">{{ currentUser.followers_count }}</p>
                                        <p class="text-gray-600 text-sm">متابِعون</p>
                                    </div>
                                </div>
                            </div>
                            
                            <button @click="showNewPostModal = true"
                                    class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded-full mb-4 transition">
                                <i class="fas fa-feather-alt ml-2"></i> تغريدة جديدة
                            </button>
                            
                            <!-- Trends Section -->
                            <div class="bg-gray-50 rounded-lg p-4">
                                <h4 class="font-bold mb-3">المواضيع الرائجة</h4>
                                <ul>
                                    <li v-for="trend in trends" :key="trend.id" class="mb-2">
                                        <a href="#" class="text-blue-500 hover:underline">#{{ trend.name }}</a>
                                        <p class="text-gray-600 text-sm">{{ trend.count }} تغريدة</p>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <!-- Main Feed -->
                    <div class="lg:col-span-2">
                        <!-- New Post Form Modal -->
                        <div v-if="showNewPostModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                                <div class="flex justify-between items-center mb-4">
                                    <h3 class="text-lg font-bold">إنشاء تغريدة</h3>
                                    <button @click="showNewPostModal = false" class="text-gray-400 hover:text-gray-600">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                                
                                <div class="mb-4">
                                    <textarea v-model="newPostContent" 
                                              placeholder="ما الذي يدور في ذهنك؟"
                                              rows="4"
                                              class="w-full px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500"></textarea>
                                </div>
                                
                                <div class="mb-4">
                                    <label class="block text-gray-700 text-sm font-bold mb-2">إضافة وسائط</label>
                                    <div class="flex space-x-2">
                                        <button @click="addImage" class="p-2 bg-gray-100 rounded-lg hover:bg-gray-200">
                                            <i class="fas fa-image text-green-500"></i>
                                        </button>
                                        <button @click="addVideo" class="p-2 bg-gray-100 rounded-lg hover:bg-gray-200">
                                            <i class="fas fa-video text-purple-500"></i>
                                        </button>
                                    </div>
                                    
                                    <div v-if="postImage" class="mt-2">
                                        <img :src="postImage" class="max-w-full h-48 object-cover rounded-lg">
                                        <button @click="postImage = null" class="text-red-500 text-sm mt-1">
                                            <i class="fas fa-times ml-1"></i> إزالة الصورة
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="flex justify-end">
                                    <button @click="createPost" 
                                            :disabled="!newPostContent"
                                            class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full disabled:opacity-50">
                                        نشر التغريدة
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Posts Feed -->
                        <div v-if="currentView === 'home'">
                            <div class="bg-white rounded-lg shadow mb-6">
                                <!-- Quick Post Input -->
                                <div class="p-4 border-b">
                                    <div class="flex">
                                        <img :src="currentUser.profile_image || '/static/images/default-profile.png'" 
                                             class="h-12 w-12 rounded-full object-cover">
                                        <textarea v-model="quickPostContent"
                                                  placeholder="ما الذي يدور في ذهنك؟"
                                                  rows="2"
                                                  class="flex-1 mr-3 px-3 py-2 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500"></textarea>
                                    </div>
                                    <div class="flex justify-between items-center mt-3">
                                        <div class="flex space-x-2">
                                            <button @click="addImageToQuickPost" class="text-green-500 hover:text-green-600">
                                                <i class="fas fa-image"></i>
                                            </button>
                                            <button @click="addVideoToQuickPost" class="text-purple-500 hover:text-purple-600">
                                                <i class="fas fa-video"></i>
                                            </button>
                                        </div>
                                        <button @click="createQuickPost"
                                                :disabled="!quickPostContent"
                                                class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full disabled:opacity-50">
                                            تغريد
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <!-- Posts List -->
                            <div v-for="post in posts" :key="post.id" class="bg-white rounded-lg shadow mb-4 post-card">
                                <div class="p-4">
                                    <div class="flex">
                                        <!-- User Avatar -->
                                        <img :src="post.user.profile_image || '/static/images/default-profile.png'" 
                                             @click="viewUserProfile(post.user)"
                                             class="h-12 w-12 rounded-full object-cover cursor-pointer">
                                        
                                        <!-- Post Content -->
                                        <div class="flex-1 mr-3">
                                            <div class="flex justify-between">
                                                <div>
                                                    <h4 class="font-bold">@{{ post.user.username }}</h4>
                                                    <p class="text-gray-600 text-sm">{{ formatDate(post.created_at) }}</p>
                                                </div>
                                                <button class="text-gray-400 hover:text-gray-600">
                                                    <i class="fas fa-ellipsis-h"></i>
                                                </button>
                                            </div>
                                            
                                            <p class="mt-2">{{ post.content }}</p>
                                            
                                            <!-- Post Media -->
                                            <div v-if="post.image" class="mt-3">
                                                <img :src="post.image" class="max-w-full h-auto rounded-lg">
                                            </div>
                                            <div v-if="post.video" class="mt-3">
                                                <video controls class="max-w-full h-auto rounded-lg">
                                                    <source :src="post.video" type="video/mp4">
                                                </video>
                                            </div>
                                            
                                            <!-- Post Actions -->
                                            <div class="flex justify-between mt-4 pt-3 border-t">
                                                <button @click="toggleLike(post)"
                                                        :class="{'text-red-500': post.liked, 'text-gray-500': !post.liked}"
                                                        class="hover:text-red-600">
                                                    <i class="far fa-heart ml-1"></i>
                                                    <span>{{ post.likes_count }}</span>
                                                </button>
                                                <button @click="toggleCommentSection(post)"
                                                        class="text-gray-500 hover:text-blue-600">
                                                    <i class="far fa-comment ml-1"></i>
                                                    <span>{{ post.comments_count }}</span>
                                                </button>
                                                <button class="text-gray-500 hover:text-green-600">
                                                    <i class="fas fa-retweet ml-1"></i>
                                                    <span>{{ post.shares_count }}</span>
                                                </button>
                                            </div>
                                            
                                            <!-- Comments Section -->
                                            <div v-if="post.showComments" class="mt-4">
                                                <div class="flex mb-4">
                                                    <img :src="currentUser.profile_image || '/static/images/default-profile.png'" 
                                                         class="h-8 w-8 rounded-full object-cover">
                                                    <div class="flex-1 mr-2">
                                                        <textarea v-model="newCommentContent[post.id]" 
                                                                  placeholder="اكتب تعليقًا..."
                                                                  rows="1"
                                                                  class="w-full px-3 py-1 text-gray-700 border rounded-lg focus:outline-none focus:border-blue-500"></textarea>
                                                        <button @click="addComment(post)"
                                                                :disabled="!newCommentContent[post.id]"
                                                                class="mt-1 bg-blue-500 hover:bg-blue-600 text-white text-sm py-1 px-3 rounded-full disabled:opacity-50">
                                                            تعليق
                                                        </button>
                                                    </div>
                                                </div>
                                                
                                                <!-- Comments List -->
                                                <div v-for="comment in post.comments" :key="comment.id" class="mr-10 mb-3">
                                                    <div class="flex">
                                                        <img :src="comment.user.profile_image || '/static/images/default-profile.png'" 
                                                             class="h-6 w-6 rounded-full object-cover">
                                                        <div class="mr-2">
                                                            <span class="font-bold text-sm">@{{ comment.user.username }}</span>
                                                            <p class="text-sm">{{ comment.content }}</p>
                                                            <div class="flex space-x-3 text-xs text-gray-500 mt-1">
                                                                <span>{{ formatDate(comment.created_at) }}</span>
                                                                <button @click="toggleLikeComment(comment)"
                                                                        :class="{'text-red-500': comment.liked}">
                                                                    إعجاب ({{ comment.likes_count }})
                                                                </button>
                                                                <button @click="replyToComment(comment, post)">
                                                                    رد
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Profile View -->
                        <div v-if="currentView === 'profile'">
                            <div class="bg-white rounded-lg shadow mb-6">
                                <!-- Profile Header -->
                                <div class="relative">
                                    <img :src="profileUser.cover_image || '/static/images/default-cover.jpg'" 
                                         class="h-48 w-full object-cover rounded-t-lg">
                                    <img :src="profileUser.profile_image || '/static/images/default-profile.png'" 
                                         class="absolute bottom-0 right-6 transform translate-y-1/2 h-32 w-32 rounded-full border-4 border-white object-cover">
                                </div>
                                
                                <div class="p-6 pt-16">
                                    <div class="flex justify-between items-start">
                                        <div>
                                            <h2 class="text-2xl font-bold">@{{ profileUser.username }}</h2>
                                            <p class="text-gray-600">{{ profileUser.bio }}</p>
                                            <p class="text-gray-500 mt-2">
                                                <i class="fas fa-map-marker-alt ml-1"></i>
                                                {{ profileUser.location }}
                                            </p>
                                        </div>
                                        
                                        <div>
                                            <button v-if="!isCurrentUserProfile" 
                                                    @click="toggleFollow(profileUser)"
                                                    :class="{'bg-gray-200 hover:bg-gray-300': profileUser.is_following, 'bg-blue-500 hover:bg-blue-600 text-white': !profileUser.is_following}"
                                                    class="font-bold py-2 px-4 rounded-full">
                                                {{ profileUser.is_following ? 'متابَع' : 'متابعة' }}
                                            </button>
                                            <button v-else
                                                    @click="changeView('settings')"
                                                    class="bg-gray-200 hover:bg-gray-300 font-bold py-2 px-4 rounded-full">
                                                تعديل الملف الشخصي
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="flex space-x-6 mt-4">
                                        <div>
                                            <span class="font-bold">{{ profileUser.following_count }}</span>
                                            <span class="text-gray-600 mr-1">متابَعون</span>
                                        </div>
                                        <div>
                                            <span class="font-bold">{{ profileUser.followers_count }}</span>
                                            <span class="text-gray-600 mr-1">متابِعون</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Sidebar -->
                    <div class="lg:col-span-1">
                        <!-- Who to Follow -->
                        <div class="bg-white rounded-lg shadow p-4 mb-6">
                            <h4 class="font-bold mb-4">من قد تتابع</h4>
                            <div class="space-y-4">
                                <div v-for="user in suggestedUsers" :key="user.id" class="flex items-center">
                                    <img :src="user.profile_image || '/static/images/default-profile.png'" 
                                         class="h-10 w-10 rounded-full object-cover">
                                    <div class="flex-1 mr-3">
                                        <h5 class="font-bold text-sm">@{{ user.username }}</h5>
                                        <p class="text-gray-600 text-xs">{{ user.bio }}</p>
                                    </div>
                                    <button @click="toggleFollow(user)"
                                            :class="{'bg-gray-200 hover:bg-gray-300': user.is_following, 'bg-blue-500 hover:bg-blue-600 text-white': !user.is_following}"
                                            class="text-xs py-1 px-3 rounded-full">
                                        {{ user.is_following ? 'متابَع' : 'متابعة' }}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Error Message -->
    <div v-else-if="error" class="flex items-center justify-center h-screen">
        <div class="text-center">
            <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
            <h2 class="text-2xl font-bold text-gray-800 mb-2">{{ error }}</h2>
            <button @click="initializeApp" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
                المحاولة مرة أخرى
            </button>
        </div>
    </div>
    `
});
