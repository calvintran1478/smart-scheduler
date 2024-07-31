<template>
  <ion-page>
    <ion-content class="ion-padding">
      <h1 class="title">Tasks to get done</h1>
      <ion-list>
        <ion-item v-for="task in tasks" :key="task.task_id">
          <ion-label>
            <h2>{{ task.name }}</h2>
            <p>
              Due: {{ task.deadline.split("T")[0] }} at
              {{ task.deadline.split("T")[1].split("-")[0] }}
            </p>
            <p v-if="task.tag">
              Tag: {{ task.tag.name }}
              <span :style="{ color: task.tag.colour }">●</span>
            </p>
          </ion-label>
          <ion-button slot="end" @click="editTask(task)">Edit</ion-button>
          <ion-button slot="end" color="danger" @click="deleteTask(task)"
            >Delete</ion-button
          >
        </ion-item>
      </ion-list>
      <ion-fab vertical="bottom" horizontal="end" slot="fixed">
        <ion-fab-button @click="openModal">
          <ion-icon :icon="addOutline"></ion-icon>
        </ion-fab-button>
      </ion-fab>
      <task-modal
        v-if="isModalOpen"
        @close="closeModal"
        @task-created="addTask"
      ></task-modal>
      <task-edit-modal
        v-if="isEditModalOpen"
        :task="selectedTask"
        @close="closeEditModal"
      />
      <ion-alert
        v-if="isDeleteAlertOpen"
        header="Confirm Delete"
        message="Are you sure you want to delete this task?"
        :buttons="[
          {
            text: 'Cancel',
            role: 'cancel',
            handler: () => {
              isDeleteAlertOpen.value = false;
            },
          },
          {
            text: 'Delete',
            role: 'destructive',
            handler: deleteConfirmedTask,
          },
        ]"
      />
    </ion-content>
  </ion-page>
</template>
  
  <script>
import {
  IonContent,
  IonHeader,
  IonPage,
  IonToolbar,
  IonTitle,
  IonList,
  IonItem,
  IonLabel,
  IonFab,
  IonFabButton,
  IonIcon,
  IonButton,
  IonAlert,
} from "@ionic/vue";
import { defineComponent, ref, onMounted } from "vue";
import { addOutline } from "ionicons/icons";
import TaskModal from "./TaskModal.vue";
import TaskEditModal from "./TaskEditModal.vue";
import { refreshToken, logout } from "../services/auth";

export default defineComponent({
  components: {
    IonContent,
    IonHeader,
    IonPage,
    IonToolbar,
    IonTitle,
    IonList,
    IonItem,
    IonLabel,
    IonFab,
    IonFabButton,
    IonIcon,
    TaskModal,
    TaskEditModal,
    IonButton,
    IonAlert,
  },
  setup() {
    const tasks = ref([]);
    const isModalOpen = ref(false);
    const isEditModalOpen = ref(false);
    const isDeleteAlertOpen = ref(false);
    const selectedTask = ref(null);
    const taskToDelete = ref(null);
    const refreshed = ref(false);

    const openModal = () => {
      isModalOpen.value = true;
    };

    const closeModal = () => {
      isModalOpen.value = false;
    };

    const addTask = (task) => {
      if (Array.isArray(tasks.value)) {
        tasks.value.push(task);
      } else {
        tasks.value = [task];
      }
    };

    const editTask = (task) => {
      selectedTask.value = task;
      isEditModalOpen.value = true;
    };

    const deleteTask = (task) => {
      taskToDelete.value = task;
      isDeleteAlertOpen.value = true;
    };

    const deleteConfirmedTask = async () => {
      const task = taskToDelete.value;
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        return;
      }
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/users/tasks/${task.task_id}`,
          {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            credentials: "include",
          }
        );
        if (response.status === 204) {
          tasks.value = tasks.value.filter((t) => t.task_id !== task.task_id);
          isDeleteAlertOpen.value = false;
        } else if (response.status == 401) {
            // refresh token
            if (!refreshed.value) {
              await refreshToken();
              refreshed.value = true;
              console.log('Token refresh successful.')
              // try again
              this.deleteConfirmedTask()
            } else {
              console.log('Time out.')
              logout();
            }
          } else {
          console.error("Failed to delete task:", response.statusText);
        }
      } catch (error) {
        console.error("Error deleting task:", error);
      }
    };

    const closeEditModal = () => {
      isEditModalOpen.value = false;
      fetchTasks();
    };


const fetchTasks = async () => {
  const token = localStorage.getItem("token"); 
  if (!token) {
    console.error("No token found");
    return;
  }
  
  try {
    const response = await fetch("http://localhost:8000/api/v1/users/tasks", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      credentials: "include",
    });
    
    if (response.ok) {
      const data = await response.json();
      tasks.value = data.tasks;
      console.log("Fetch tasks successful.");
      console.log(tasks.value);
    } else if (response.status == 401) {
            // refresh token
            if (!refreshed.value) {
              await refreshToken();
              refreshed.value = true;
              console.log('Token refresh successful.')
              // try again
              this.fetchTasks()
            } else {
              console.log('Time out.')
              logout();
            }
          } else {
      console.error("Failed to fetch tasks: ", response.status, response.statusText);
    }
  } catch (err) {
    console.error("Failed to fetch tasks:", err);
  }
};

onMounted(() => {
  fetchTasks();
});


    return {
      tasks,
      isModalOpen,
      isEditModalOpen,
      isDeleteAlertOpen,
      selectedTask,
      taskToDelete,
      openModal,
      closeModal,
      addTask,
      editTask,
      closeEditModal,
      deleteTask,
      deleteConfirmedTask,
      addOutline,
    };
  },
});
</script>
  
  <style scoped>
/* styling later */
.title {
  padding-top: 30px;
  font-size: 28px;
  font-weight: bold;
  text-align: left;
  padding-left: 25px;
}
</style>
  